#!/usr/bin/env python3
"""
chatgpt-distiller — Extract vision, decisions, and preferences from ChatGPT exports.

Parses OpenAI's conversations.json export, filters for high-signal conversations,
extracts structured insights via Claude Haiku, and emits to Claude Code memory
files + AKOS-compatible knowledge units.

Usage:
    python chatgpt_distiller.py scan "path/to/conversations.json"
    python chatgpt_distiller.py distill "path/to/conversations.json"
    python chatgpt_distiller.py distill "path/to/conversations.json" --dry-run --limit 50
    python chatgpt_distiller.py update "path/to/new_export.json"
    python chatgpt_distiller.py rebuild
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MEMORY_DIR = Path.home() / ".claude" / "memory"
VISION_DIR = MEMORY_DIR / "chatgpt_vision"
MANIFEST_FILE = VISION_DIR / "_manifest.json"
GLOBAL_MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"

AKOS_DIR = Path.home() / "Desktop" / "Cursor Projects" / "AKOS" / "datasets" / "canonical" / "chatgpt"

# Signal scoring weights
SIGNAL_WEIGHTS = {
    "vision": 3.0,
    "decision": 2.5,
    "preference": 2.0,
    "expertise": 1.5,
    "project": 1.0,
}

# High-signal keyword patterns (compiled once)
VISION_PATTERNS = re.compile(
    r"\b("
    r"i want to build|the goal is|my strategy|long[- ]term|architecture should|"
    r"the system needs|my vision|end goal|roadmap|milestone|big picture|"
    r"quiero construir|la meta es|mi estrategia|mi visión|objetivo final|"
    r"the dream is|ultimate goal|north star|what i.m building|the plan is"
    r")\b", re.IGNORECASE
)

DECISION_PATTERNS = re.compile(
    r"\b("
    r"i decided|we should use|let.s go with|the approach is|i chose|"
    r"i.m going with|we.ll use|the stack is|i picked|switching to|"
    r"decidí|vamos a usar|el approach es|elegí|voy con"
    r")\b", re.IGNORECASE
)

PREFERENCE_PATTERNS = re.compile(
    r"\b("
    r"i prefer|always use|never do|my style|i like to|i hate when|"
    r"don.t ever|i always want|my workflow|prefiero|siempre uso|nunca hagas|"
    r"mi estilo|the way i work"
    r")\b", re.IGNORECASE
)

EXPERTISE_PATTERNS = re.compile(
    r"\b("
    r"in my experience|what i.ve learned|the trick is|pro tip|"
    r"a common mistake|the key insight|what most people miss|"
    r"en mi experiencia|lo que aprendí|el truco es"
    r")\b", re.IGNORECASE
)

PROJECT_PATTERNS = re.compile(
    r"\b("
    r"kobiisports|kobiicraft|kobiiclaw|kobiiai|pa[- ]template|"
    r"akos|tuax|mundcraft|costaluz|nexumops|"
    r"wii homebrew|kamek|caddie|"
    r"saas launch|personal assistant"
    r")\b", re.IGNORECASE
)

# Low-signal indicators
NOISE_PATTERNS = re.compile(
    r"(traceback|error:|exception:|stacktrace|syntax error|"
    r"fix this|debug this|why doesn.t|what.s wrong|"
    r"```[\s\S]{500,}```"  # Large code blocks
    r")", re.IGNORECASE
)

# AKOS domain keywords (subset — matches knowledge_engine.py)
AKOS_DOMAINS = {
    "ecommerce": ["ecommerce", "shopify", "amazon", "dropship", "conversion rate", "aov", "ltv"],
    "sales": ["sales", "selling", "close", "closing", "objection", "pitch", "pipeline"],
    "outreach": ["outreach", "cold email", "email sequence", "response rate", "lead gen", "funnel"],
    "marketing": ["marketing", "brand", "campaign", "audience", "advertising", "growth marketing"],
    "seo": ["seo", "search engine", "ranking", "backlink", "organic traffic", "ai search"],
    "social_media": ["social media", "instagram", "tiktok", "reels", "viral", "ugc", "creator"],
    "scaling": ["scaling", "scale", "systemiz", "automat", "delegation", "sop", "hiring", "operations"],
    "wealth": ["invest", "wealth", "real estate", "stock", "crypto", "passive income", "net worth"],
    "mindset": ["mindset", "discipline", "habit", "focus", "motivation", "goal setting", "vision"],
    "ai_automation": ["ai agent", "automation", "workflow", "claude", "gpt", "llm", "prompt", "mcp", "pipeline"],
    "copywriting": ["copywriting", "headline", "hook", "cta", "persuasion", "ad copy"],
    "saas": ["saas", "software", "subscription", "mrr", "churn", "retention", "freemium"],
    "gaming": ["gaming", "game", "minecraft", "server", "modding", "wii", "homebrew"],
}

# Insight types for extraction
INSIGHT_TYPES = ["VISION", "DECISION", "PREFERENCE", "EXPERTISE", "PROJECT"]

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A single message from a ChatGPT conversation."""
    content: str
    role: str  # user, assistant, system, tool
    timestamp: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class Conversation:
    """A parsed ChatGPT conversation with signal scoring."""
    id: str
    title: str
    messages: list[Message] = field(default_factory=list)
    create_time: Optional[float] = None
    update_time: Optional[float] = None
    # Scoring
    signal_score: float = 0.0
    signal_breakdown: dict = field(default_factory=dict)
    user_message_count: int = 0
    total_tokens_estimate: int = 0

    @property
    def user_text(self) -> str:
        """Concatenated user messages — where the signal lives."""
        return "\n".join(m.content for m in self.messages if m.role == "user")

    @property
    def full_text(self) -> str:
        """All messages concatenated."""
        return "\n".join(m.content for m in self.messages)


@dataclass
class Insight:
    """An extracted insight from a conversation."""
    type: str  # VISION, DECISION, PREFERENCE, EXPERTISE, PROJECT
    content: str
    confidence: float  # 0.0 - 1.0
    domains: list[str] = field(default_factory=list)
    source_conversation: str = ""  # conversation title
    source_id: str = ""  # conversation id
    timestamp: Optional[str] = None

    def to_akos_unit(self) -> dict:
        """Convert to AKOS-compatible JSON unit."""
        return {
            "id": f"chatgpt-{uuid.uuid4()}",
            "type": self.type.lower(),
            "content": self.content,
            "tags": self.domains[:5],
            "source": f"chatgpt-export",
            "origin_file": f"conversations.json:{self.source_conversation}",
            "confidence_score": round(self.confidence, 2),
            "tier": 1 if self.confidence >= 0.8 else (2 if self.confidence >= 0.5 else 3),
            "created_at": self.timestamp or datetime.now(timezone.utc).isoformat(),
            "checksum": hashlib.sha256(self.content.encode()).hexdigest(),
        }


# ---------------------------------------------------------------------------
# Stage 1: PARSE
# ---------------------------------------------------------------------------

def parse_conversations(filepath: str) -> list[Conversation]:
    """Parse ChatGPT conversations.json export file.

    Replicates the mapping traversal from PA-Template's chatgpt.ts parser.
    Handles large files by loading once (stdlib json is faster than streaming
    for files under 1GB; for larger files, user should split first).
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[error] File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    file_size_mb = path.stat().st_size / (1024 * 1024)
    print(f"[parse] Reading {filepath} ({file_size_mb:.1f} MB)...")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[error] Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    if not isinstance(data, list):
        print("[error] Expected a JSON array of conversations", file=sys.stderr)
        sys.exit(1)

    conversations = []
    skipped = 0

    for conv_data in data:
        mapping = conv_data.get("mapping")
        if not mapping:
            skipped += 1
            continue

        conv = Conversation(
            id=conv_data.get("id", str(uuid.uuid4())),
            title=conv_data.get("title", "Untitled"),
            create_time=conv_data.get("create_time"),
            update_time=conv_data.get("update_time"),
        )

        for node in mapping.values():
            msg_data = node.get("message")
            if not msg_data:
                continue

            content_data = msg_data.get("content")
            if not content_data:
                continue

            parts = content_data.get("parts", [])
            text = "\n".join(
                p for p in parts if isinstance(p, str)
            ).strip()

            if not text:
                continue

            role = "unknown"
            author = msg_data.get("author")
            if author:
                role = author.get("role", "unknown")

            create_time = msg_data.get("create_time")
            timestamp = None
            if create_time:
                try:
                    timestamp = datetime.fromtimestamp(
                        create_time, tz=timezone.utc
                    ).isoformat()
                except (ValueError, OSError):
                    pass

            conv.messages.append(Message(
                content=text,
                role=role,
                timestamp=timestamp,
                message_id=msg_data.get("id"),
            ))

        if conv.messages:
            conv.user_message_count = sum(
                1 for m in conv.messages if m.role == "user"
            )
            conv.total_tokens_estimate = estimate_tokens(conv.full_text)
            conversations.append(conv)
        else:
            skipped += 1

    print(f"[parse] Parsed {len(conversations)} conversations ({skipped} skipped)")
    return conversations


def estimate_tokens(text: str) -> int:
    """Rough token estimate: words * 1.3 for English/Spanish mix."""
    return int(len(text.split()) * 1.3)


# ---------------------------------------------------------------------------
# Stage 2: FILTER (signal scoring)
# ---------------------------------------------------------------------------

def score_conversations(conversations: list[Conversation]) -> list[Conversation]:
    """Score each conversation by signal density. Higher = more insight-rich."""
    for conv in conversations:
        user_text = conv.user_text
        if not user_text:
            conv.signal_score = 0.0
            continue

        breakdown = {}

        # Pattern-based scoring on USER messages (where vision lives)
        vision_hits = len(VISION_PATTERNS.findall(user_text))
        decision_hits = len(DECISION_PATTERNS.findall(user_text))
        preference_hits = len(PREFERENCE_PATTERNS.findall(user_text))
        expertise_hits = len(EXPERTISE_PATTERNS.findall(user_text))
        project_hits = len(PROJECT_PATTERNS.findall(user_text))

        breakdown["vision"] = vision_hits * SIGNAL_WEIGHTS["vision"]
        breakdown["decision"] = decision_hits * SIGNAL_WEIGHTS["decision"]
        breakdown["preference"] = preference_hits * SIGNAL_WEIGHTS["preference"]
        breakdown["expertise"] = expertise_hits * SIGNAL_WEIGHTS["expertise"]
        breakdown["project"] = project_hits * SIGNAL_WEIGHTS["project"]

        # Bonus: longer user engagement = deeper discussion
        if conv.user_message_count >= 10:
            breakdown["depth"] = 2.0
        elif conv.user_message_count >= 5:
            breakdown["depth"] = 1.0
        else:
            breakdown["depth"] = 0.0

        # Penalty: high noise ratio
        noise_hits = len(NOISE_PATTERNS.findall(conv.full_text))
        breakdown["noise_penalty"] = -noise_hits * 1.5

        # Penalty: very short conversations (< 3 user messages)
        if conv.user_message_count < 3:
            breakdown["short_penalty"] = -3.0
        else:
            breakdown["short_penalty"] = 0.0

        conv.signal_breakdown = breakdown
        conv.signal_score = max(0.0, sum(breakdown.values()))

    # Sort descending by signal score
    conversations.sort(key=lambda c: c.signal_score, reverse=True)
    return conversations


def classify_domains(text: str) -> list[str]:
    """Classify text into AKOS domains using keyword matching."""
    text_lower = text.lower()
    domains = []
    for domain, keywords in AKOS_DOMAINS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches >= 2:
            domains.append(domain)
    return domains


# ---------------------------------------------------------------------------
# Stage 3: EXTRACT (LLM pass)
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """You are analyzing a ChatGPT conversation to extract the USER's vision, decisions, preferences, and expertise. Focus ONLY on what the USER said — their messages reveal their thinking.

Extract ONLY these insight types if present:
1. VISION — What the user wants to build/achieve long-term
2. DECISION — Technical or strategic decisions made (with reasoning)
3. PREFERENCE — User preferences about tools, patterns, style, workflow
4. EXPERTISE — Domain knowledge the user demonstrated
5. PROJECT — Project names, relationships, status updates

Rules:
- Extract from USER messages only (assistant responses are noise)
- Each insight should be 1-3 sentences, self-contained
- Skip debugging back-and-forth, one-off questions, iterative prompt tuning
- If the conversation contains NO signal, return an empty array
- Be concise but preserve the user's original intent and reasoning
- Include both English and Spanish content (the user is bilingual)

Output as a JSON array:
[{{"type": "VISION|DECISION|PREFERENCE|EXPERTISE|PROJECT", "content": "...", "confidence": 0.0-1.0}}]

If no insights found, output: []

Conversation title: {title}
---
{conversation_text}"""


def extract_insights_batch(
    conversations: list[Conversation],
    api_key: Optional[str] = None,
    model: str = "claude-haiku-4-5-20251001",
) -> list[Insight]:
    """Extract structured insights from conversations using Claude API.

    API key resolution order:
    1. Explicit api_key parameter (from --api-key CLI flag)
    2. ANTHROPIC_API_KEY environment variable
    3. anthropic SDK default resolution
    """
    try:
        import anthropic
    except ImportError:
        print("[error] anthropic SDK not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    # Let the SDK handle key resolution (env var, config file, etc.)
    try:
        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    except anthropic.AuthenticationError:
        print("[error] No API key found. Set the ANTHROPIC_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)
    all_insights = []

    for i, conv in enumerate(conversations):
        # Build conversation text (user messages only for token efficiency)
        conv_lines = []
        for msg in conv.messages:
            if msg.role == "user":
                conv_lines.append(f"USER: {msg.content}")
            elif msg.role == "assistant":
                # Include a truncated version for context
                truncated = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                conv_lines.append(f"ASSISTANT: {truncated}")

        conv_text = "\n\n".join(conv_lines)

        # Truncate if too long (keep under 100K tokens)
        max_chars = 300_000  # ~75K tokens
        if len(conv_text) > max_chars:
            conv_text = conv_text[:max_chars] + "\n\n[TRUNCATED]"

        prompt = EXTRACTION_PROMPT.format(
            title=conv.title,
            conversation_text=conv_text,
        )

        try:
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Parse JSON from response (handle markdown code blocks)
            json_match = re.search(r"\[[\s\S]*\]", response_text)
            if json_match:
                raw_insights = json.loads(json_match.group())
            else:
                raw_insights = []

            for raw in raw_insights:
                insight = Insight(
                    type=raw.get("type", "VISION"),
                    content=raw.get("content", ""),
                    confidence=raw.get("confidence", 0.5),
                    domains=classify_domains(raw.get("content", "")),
                    source_conversation=conv.title,
                    source_id=conv.id,
                    timestamp=conv.messages[0].timestamp if conv.messages else None,
                )
                all_insights.append(insight)

            print(f"  [{i+1}/{len(conversations)}] {conv.title[:50]} -> {len(raw_insights)} insights")

        except Exception as e:
            print(f"  [{i+1}/{len(conversations)}] {conv.title[:50]} -> ERROR: {e}")

    return all_insights


# ---------------------------------------------------------------------------
# Stage 4: DEDUP (TF-IDF cosine similarity)
# ---------------------------------------------------------------------------

def deduplicate_insights(insights: list[Insight], threshold: float = 0.80) -> list[Insight]:
    """Remove near-duplicate insights using TF-IDF cosine similarity."""
    if len(insights) <= 1:
        return insights

    # Build vocabulary
    docs = [insight.content.lower().split() for insight in insights]
    vocab = {}
    for doc in docs:
        for word in set(doc):
            vocab[word] = vocab.get(word, 0) + 1

    # IDF
    n_docs = len(docs)
    idf = {word: math.log(n_docs / count) for word, count in vocab.items()}

    # TF-IDF vectors (sparse — just dicts)
    vectors = []
    for doc in docs:
        tf = Counter(doc)
        total = len(doc) if doc else 1
        vec = {word: (count / total) * idf.get(word, 0) for word, count in tf.items()}
        vectors.append(vec)

    def cosine_sim(a: dict, b: dict) -> float:
        common = set(a.keys()) & set(b.keys())
        if not common:
            return 0.0
        dot = sum(a[k] * b[k] for k in common)
        mag_a = math.sqrt(sum(v * v for v in a.values()))
        mag_b = math.sqrt(sum(v * v for v in b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    # Greedy dedup: keep higher-confidence insight when similar
    keep = [True] * len(insights)
    for i in range(len(insights)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(insights)):
            if not keep[j]:
                continue
            sim = cosine_sim(vectors[i], vectors[j])
            if sim >= threshold:
                # Keep the one with higher confidence
                if insights[i].confidence >= insights[j].confidence:
                    keep[j] = False
                else:
                    keep[i] = False
                    break

    deduped = [ins for ins, k in zip(insights, keep) if k]
    removed = len(insights) - len(deduped)
    if removed > 0:
        print(f"[dedup] Removed {removed} near-duplicates (threshold={threshold})")
    return deduped


# ---------------------------------------------------------------------------
# Stage 5: CLASSIFY (already done inline during extraction)
# Stage 6: EMIT
# ---------------------------------------------------------------------------

def emit_memory_files(insights: list[Insight]) -> None:
    """Write insights to Claude Code memory files with proper frontmatter."""
    VISION_DIR.mkdir(parents=True, exist_ok=True)

    # Group by type
    by_type: dict[str, list[Insight]] = {}
    for ins in insights:
        by_type.setdefault(ins.type, []).append(ins)

    # Sort each group by confidence descending
    for group in by_type.values():
        group.sort(key=lambda x: x.confidence, reverse=True)

    files_written = []

    # Vision core
    if "VISION" in by_type:
        content = _render_memory_file(
            name="Vision Core — ChatGPT History",
            description="Long-term goals and vision extracted from ChatGPT conversations",
            mem_type="user",
            insights=by_type["VISION"][:30],
        )
        (VISION_DIR / "vision_core.md").write_text(content, encoding="utf-8")
        files_written.append("vision_core.md")

    # Technical decisions
    if "DECISION" in by_type:
        tech = [i for i in by_type["DECISION"] if _is_technical(i.content)]
        strat = [i for i in by_type["DECISION"] if not _is_technical(i.content)]

        if tech:
            content = _render_memory_file(
                name="Technical Decisions — ChatGPT History",
                description="Stack choices, architecture patterns, tool preferences from ChatGPT",
                mem_type="reference",
                insights=tech[:40],
            )
            (VISION_DIR / "decisions_technical.md").write_text(content, encoding="utf-8")
            files_written.append("decisions_technical.md")

        if strat:
            content = _render_memory_file(
                name="Strategic Decisions — ChatGPT History",
                description="Business and product decisions from ChatGPT conversations",
                mem_type="reference",
                insights=strat[:20],
            )
            (VISION_DIR / "decisions_strategic.md").write_text(content, encoding="utf-8")
            files_written.append("decisions_strategic.md")

    # Preferences
    if "PREFERENCE" in by_type:
        content = _render_memory_file(
            name="Preferences — ChatGPT History",
            description="Coding style, workflow, and communication preferences from ChatGPT",
            mem_type="feedback",
            insights=by_type["PREFERENCE"][:25],
        )
        (VISION_DIR / "preferences.md").write_text(content, encoding="utf-8")
        files_written.append("preferences.md")

    # Expertise
    if "EXPERTISE" in by_type:
        content = _render_memory_file(
            name="Domain Expertise — ChatGPT History",
            description="Domain knowledge and expertise demonstrated in ChatGPT conversations",
            mem_type="user",
            insights=by_type["EXPERTISE"][:20],
        )
        (VISION_DIR / "expertise.md").write_text(content, encoding="utf-8")
        files_written.append("expertise.md")

    # Project map
    if "PROJECT" in by_type:
        content = _render_memory_file(
            name="Project Map — ChatGPT History",
            description="Project relationships, status, and context from ChatGPT conversations",
            mem_type="project",
            insights=by_type["PROJECT"][:25],
        )
        (VISION_DIR / "project_map.md").write_text(content, encoding="utf-8")
        files_written.append("project_map.md")

    print(f"[emit] Wrote {len(files_written)} memory files to {VISION_DIR}")
    return files_written


def _render_memory_file(name: str, description: str, mem_type: str, insights: list[Insight]) -> str:
    """Render a Claude memory file with YAML frontmatter."""
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        f"type: {mem_type}",
        "---",
        "",
    ]
    for ins in insights:
        domain_tag = f" [{', '.join(ins.domains[:3])}]" if ins.domains else ""
        confidence_tag = f" (conf: {ins.confidence:.0%})" if ins.confidence < 0.8 else ""
        lines.append(f"- {ins.content}{domain_tag}{confidence_tag}")

    return "\n".join(lines) + "\n"


def _is_technical(text: str) -> bool:
    """Heuristic: does this text discuss technical topics?"""
    tech_words = {"api", "stack", "framework", "database", "deploy", "architecture",
                  "code", "server", "frontend", "backend", "sdk", "library", "repo",
                  "git", "docker", "elixir", "python", "typescript", "react", "next.js",
                  "prisma", "kamek", "gx", "wii", "mcp", "claude"}
    return any(w in text.lower() for w in tech_words)


def emit_akos_units(insights: list[Insight]) -> None:
    """Write insights as AKOS-compatible JSON units."""
    AKOS_DIR.mkdir(parents=True, exist_ok=True)

    units = [ins.to_akos_unit() for ins in insights]
    output_path = AKOS_DIR / "chatgpt_insights.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(units, f, indent=2, ensure_ascii=False)

    print(f"[emit] Wrote {len(units)} AKOS units to {output_path}")


def update_memory_index(files_written: list[str]) -> None:
    """Add chatgpt_vision entries to ~/.claude/memory/MEMORY.md if not already present."""
    if not GLOBAL_MEMORY_INDEX.exists():
        return

    content = GLOBAL_MEMORY_INDEX.read_text(encoding="utf-8")

    if "chatgpt_vision" in content:
        print("[index] MEMORY.md already has chatgpt_vision entries — skipping")
        return

    entries = [
        "",
        "## ChatGPT Vision Context (distilled)",
    ]

    file_descriptions = {
        "vision_core.md": "Long-term vision and goals",
        "decisions_technical.md": "Technical stack and architecture decisions",
        "decisions_strategic.md": "Business and product strategy decisions",
        "preferences.md": "Coding style, workflow, communication preferences",
        "expertise.md": "Domain expertise demonstrated",
        "project_map.md": "Project relationships and context",
    }

    for fname in files_written:
        desc = file_descriptions.get(fname, fname)
        entries.append(f"- [{desc}](chatgpt_vision/{fname}) — extracted from ChatGPT history")

    new_content = content.rstrip() + "\n" + "\n".join(entries) + "\n"
    GLOBAL_MEMORY_INDEX.write_text(new_content, encoding="utf-8")
    print(f"[index] Updated {GLOBAL_MEMORY_INDEX} with {len(files_written)} entries")


# ---------------------------------------------------------------------------
# Manifest (incremental updates)
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    """Load the processing manifest."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "last_processed": None,
        "conversation_ids_processed": [],
        "total_conversations": 0,
        "total_insights_extracted": 0,
        "export_file_hash": None,
    }


def save_manifest(manifest: dict) -> None:
    """Save the processing manifest."""
    VISION_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def file_hash(filepath: str) -> str:
    """SHA256 of a file (first 10MB for speed on large exports)."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        chunk = f.read(10 * 1024 * 1024)
        h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def cmd_scan(args):
    """Scan and rank conversations by signal score (no LLM, no cost)."""
    conversations = parse_conversations(args.file)
    conversations = score_conversations(conversations)

    # Stats
    total = len(conversations)
    high_signal = [c for c in conversations if c.signal_score >= 5.0]
    medium_signal = [c for c in conversations if 2.0 <= c.signal_score < 5.0]

    print(f"\n{'='*70}")
    print(f"SIGNAL ANALYSIS — {total} conversations")
    print(f"{'='*70}")
    print(f"  High signal (>=5.0):   {len(high_signal)} conversations")
    print(f"  Medium signal (2-5):   {len(medium_signal)} conversations")
    print(f"  Low signal (<2):       {total - len(high_signal) - len(medium_signal)} conversations")
    print()

    # Show top conversations
    show = min(args.top, len(conversations))
    print(f"TOP {show} CONVERSATIONS BY SIGNAL SCORE:")
    print(f"{'-'*70}")
    print(f"{'Score':>6}  {'Msgs':>4}  {'~Tok':>6}  Title")
    print(f"{'-'*70}")

    for conv in conversations[:show]:
        title = conv.title[:50] if conv.title else "Untitled"
        print(f"{conv.signal_score:6.1f}  {conv.user_message_count:4d}  {conv.total_tokens_estimate:6d}  {title}")

        if args.verbose:
            for key, val in conv.signal_breakdown.items():
                if val != 0:
                    print(f"         {key}: {val:+.1f}")

    # Domain distribution
    print(f"\n{'='*70}")
    print("DOMAIN DISTRIBUTION (across all conversations):")
    domain_counts = Counter()
    for conv in conversations:
        if conv.signal_score >= 2.0:
            domains = classify_domains(conv.user_text)
            for d in domains:
                domain_counts[d] += 1

    for domain, count in domain_counts.most_common():
        bar = "#" * min(count, 40)
        print(f"  {domain:20s} {count:4d}  {bar}")

    # Estimate for distill
    est_convs = len(high_signal) + len(medium_signal)
    est_tokens = sum(c.total_tokens_estimate for c in conversations if c.signal_score >= 2.0)
    print(f"\n{'='*70}")
    print(f"DISTILL ESTIMATE:")
    print(f"  Conversations to process: {est_convs}")
    print(f"  Estimated input tokens:   {est_tokens:,}")
    print(f"  Estimated Haiku cost:     ~${est_tokens * 0.25 / 1_000_000:.2f}")
    print(f"\nRun: python chatgpt_distiller.py distill \"{args.file}\"")


def cmd_distill(args):
    """Full pipeline: parse -> filter -> extract -> dedup -> emit."""
    # Parse
    conversations = parse_conversations(args.file)
    conversations = score_conversations(conversations)

    # Filter
    threshold = 2.0
    candidates = [c for c in conversations if c.signal_score >= threshold]

    if args.limit:
        candidates = candidates[:args.limit]

    print(f"[filter] {len(candidates)} conversations pass signal threshold (>={threshold})")

    if args.dry_run:
        print(f"\n[dry-run] Would process {len(candidates)} conversations. Top 10:")
        for conv in candidates[:10]:
            print(f"  {conv.signal_score:5.1f}  {conv.title[:60]}")
        print(f"\nRun without --dry-run to proceed.")
        return

    if not candidates:
        print("[done] No high-signal conversations found.")
        return

    # Check manifest for incremental
    manifest = load_manifest()
    processed_ids = set(manifest.get("conversation_ids_processed", []))
    if processed_ids:
        new_candidates = [c for c in candidates if c.id not in processed_ids]
        if len(new_candidates) < len(candidates):
            print(f"[incremental] {len(candidates) - len(new_candidates)} already processed, {len(new_candidates)} new")
            candidates = new_candidates

    if not candidates:
        print("[done] All high-signal conversations already processed.")
        return

    # Extract
    print(f"\n[extract] Processing {len(candidates)} conversations via Claude Haiku...")
    api_key = getattr(args, "api_key", None)
    model = getattr(args, "model", "claude-haiku-4-5-20251001")
    insights = extract_insights_batch(candidates, api_key=api_key, model=model)
    print(f"[extract] Got {len(insights)} raw insights")

    if not insights:
        print("[done] No insights extracted.")
        return

    # Dedup
    insights = deduplicate_insights(insights)
    print(f"[dedup] {len(insights)} insights after deduplication")

    # Emit
    files_written = emit_memory_files(insights)
    emit_akos_units(insights)
    update_memory_index(files_written)

    # Update manifest
    manifest["last_processed"] = datetime.now(timezone.utc).isoformat()
    manifest["conversation_ids_processed"] = list(
        processed_ids | {c.id for c in candidates}
    )
    manifest["total_conversations"] = len(conversations)
    manifest["total_insights_extracted"] = manifest.get("total_insights_extracted", 0) + len(insights)
    manifest["export_file_hash"] = file_hash(args.file)
    save_manifest(manifest)

    # Summary
    print(f"\n{'='*70}")
    print(f"DISTILLATION COMPLETE")
    print(f"{'='*70}")
    print(f"  Conversations processed:  {len(candidates)}")
    print(f"  Insights extracted:       {len(insights)}")
    print(f"  Memory files written:     {VISION_DIR}")
    print(f"  AKOS units written:       {AKOS_DIR}")
    print(f"  Manifest updated:         {MANIFEST_FILE}")

    by_type = Counter(ins.type for ins in insights)
    for itype, count in by_type.most_common():
        print(f"    {itype}: {count}")


def cmd_update(args):
    """Incremental update — only processes new conversations."""
    # Same as distill but skips already-processed conversations
    args.dry_run = False
    args.limit = None
    cmd_distill(args)


def cmd_rebuild(args):
    """Rebuild memory files from existing AKOS units (no LLM call needed)."""
    akos_file = AKOS_DIR / "chatgpt_insights.json"
    if not akos_file.exists():
        print(f"[error] No AKOS units found at {akos_file}", file=sys.stderr)
        print("Run 'distill' first to extract insights.")
        sys.exit(1)

    with open(akos_file, "r", encoding="utf-8") as f:
        units = json.load(f)

    insights = []
    for unit in units:
        insights.append(Insight(
            type=unit.get("type", "vision").upper(),
            content=unit.get("content", ""),
            confidence=unit.get("confidence_score", 0.5),
            domains=unit.get("tags", []),
            source_conversation=unit.get("origin_file", "").split(":")[-1] if ":" in unit.get("origin_file", "") else "",
            source_id=unit.get("id", ""),
            timestamp=unit.get("created_at"),
        ))

    insights = deduplicate_insights(insights)
    files_written = emit_memory_files(insights)
    update_memory_index(files_written)
    print(f"[rebuild] Rebuilt {len(files_written)} memory files from {len(insights)} AKOS units")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract vision, decisions, and preferences from ChatGPT exports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan conversations.json              # Preview signal scores
  %(prog)s scan conversations.json --top 30     # Show top 30
  %(prog)s distill conversations.json           # Full pipeline
  %(prog)s distill conversations.json --limit 50 --dry-run
  %(prog)s update new_conversations.json        # Incremental
  %(prog)s rebuild                              # Rebuild from AKOS units
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Scan and rank conversations by signal")
    scan_parser.add_argument("file", help="Path to conversations.json")
    scan_parser.add_argument("--top", type=int, default=20, help="Show top N conversations")
    scan_parser.add_argument("--verbose", "-v", action="store_true", help="Show score breakdown")

    # distill
    distill_parser = subparsers.add_parser("distill", help="Full extraction pipeline")
    distill_parser.add_argument("file", help="Path to conversations.json")
    distill_parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    distill_parser.add_argument("--limit", type=int, help="Process only top N conversations")
    distill_parser.add_argument("--exclude", help="Regex pattern to exclude conversations")
    distill_parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="Model for extraction")
    distill_parser.add_argument("--api-key", dest="api_key", help="Anthropic API key (or set env var)")

    # update
    update_parser = subparsers.add_parser("update", help="Incremental update with new export")
    update_parser.add_argument("file", help="Path to new conversations.json")

    # rebuild
    subparsers.add_parser("rebuild", help="Rebuild memory files from AKOS units")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "scan": cmd_scan,
        "distill": cmd_distill,
        "update": cmd_update,
        "rebuild": cmd_rebuild,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
