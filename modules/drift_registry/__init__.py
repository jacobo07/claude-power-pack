"""Drift registry -- what this estate detects about drift, read off disk.

Discovery only. This package builds no detector and modifies none; it
reports which exist, which families they attribute drift to, and which
families the repo names in prose without any code mentioning them.
"""
from .registry import Detector, FamilyTerm, render, scan

__all__ = ["Detector", "FamilyTerm", "render", "scan"]
