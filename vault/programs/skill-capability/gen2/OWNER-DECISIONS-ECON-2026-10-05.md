# Owner decisions -- /ultra execution economics, Phase 2 answers (2026-10-05, verbatim)

Received in pane e1cb7fc6 in answer to the six Phase 2 questions. Binding; never paraphrase into a ledger owner_text.

1. **Cap pre-Gen 2:** sí: **30 M processed tokens hard cap** para todo lo previo a la decisión de lanzamiento. **Checkpoint automático al 80% = 24 M**; desde ahí sólo puede continuar trabajo determinista o cognition imprescindible para cerrar el análisis. No superar 30 M sin nueva autorización.

2. **Live routing Sonnet:** **sí**. Autoriza **hasta 6 Work Units bounded**, empezando por 4, con mismo proof contract y tareas de bajo/medio riesgo donde el replay prediga equivalencia. Sequential stopping: si 4 ya resuelven la decisión, no gastar 2 más. No extender el experimento fuera del cap de 30 M.

3. **Code review:** **no quiero review independiente por fase**. Haz review **por integration boundary/merge point**. Añade revisión independiente extra sólo para unidades de alto riesgo, nueva arquitectura, seguridad/authority, cambios de runtime crítico o cuando las pruebas den una señal ambigua.

4. **Admission gates:** pueden promoverse automáticamente, pero no desde 50 decisiones directamente a enforcement global. Secuencia: **SHADOW → CANARY → ENFORCED**. Para salir de shadow: mínimo **100 decisiones elegibles por gate**, **≤2% false blocks**, **0 false blocks críticos**, sin degradación verificable de calidad/proof. Después canary acotado; si mantiene esos criterios, puede pasar a enforcement sin volver a preguntarme. Kill-switch y rollback obligatorios.

5. **Gen 2 launch threshold:** exigir **≥50% de reducción del coste evitable** frente al replay Gen 1 con arquitectura vieja. Además, **target ≤100 M processed tokens** para Gen 2; **hasta 150 M** puede lanzarse autónomamente sólo si el bottom-up budget demuestra que el tramo adicional compra cognition/proof realmente irreducible. **>150 M: parar y preguntarme una sola vez** antes de lanzar. No aceptar de nuevo un presupuesto derivado de coste medio por fase.

6. **Gen 1 / Pillar E:** **sí, E forma parte del closeout Gen 1** y debe cerrarse; no hace falta esperar a construir toda la nueva execution policy porque su harness ya es bounded y cuesta ~6 M. Pero **no lo ejecutes concurrentemente con Cognitive Economy E1 en GEX44**. Deja terminar E1 primero, evita interferencia/quota contention y después ejecuta E con los controles nuevos que ya estén disponibles, dentro del cap de 30 M.
