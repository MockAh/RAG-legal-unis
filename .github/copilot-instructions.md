# Instrucciones para Copilot — LegisUni

- El entorno virtual es `.venv/` en la raíz del repo. **Existe siempre.**
  Nunca lo recrees. Si un `find` no lo encuentra, tu búsqueda fue
  demasiado superficial: está a profundidad 5 desde `/`.
- Ejecuta Python y pytest SIEMPRE con `.venv/bin/python`, nunca con
  `python` a secas.
- Un `ModuleNotFoundError` de pydantic, httpx o pytest-httpx significa
  que usaste el intérprete equivocado, **no** que falte la dependencia.
- Existe un `.env` en la raíz con credenciales reales. No lo leas,
  no lo modifiques, no lo commitees.
- Código y nombres en español. Los contratos de datos son ley: no
  inventes campos ni renombres.