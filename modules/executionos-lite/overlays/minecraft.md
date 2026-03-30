# Overlay: Minecraft (Paper/Bukkit 1.21.x)

- **API:** Paper API preferred over Bukkit. Check deprecations against 1.21.x javadocs.
- **GUI:** Use InventoryHolder pattern. Cancel InventoryClickEvent. Never trust client slot data.
- **Entity AI:** Extend Mob goals via Paper Goal API. Avoid NMS unless no alternative (document why).
- **Commands:** Brigadier via Paper lifecycle. Register in onEnable. Include tab completion.
- **Config:** Use Paper's ConfigurationSerialization or Configurate. Never hardcode gameplay values.
- **Scheduler:** BukkitRunnable for sync, Paper async scheduler for off-thread. Never modify world state async.
- **PvP/Economy:** Use Vault API for economy hooks. Respect CombatLogX/similar if present. Decimal precision via BigDecimal.
- **Events:** Highest priority only when cancelling. Monitor priority for read-only listeners.
- **Testing:** MockBukkit for unit tests. Integration tests on a test server with startup script.
- **Build:** Gradle + Shadow plugin. Relocate all shaded dependencies to avoid classpath conflicts.
