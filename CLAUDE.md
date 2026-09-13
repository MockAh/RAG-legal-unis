# Acervo — instrucciones para Claude Code

## Entorno (no negociable)
- El venv es `.venv/` en la raíz. **Existe siempre.** Nunca lo recrees.
- Ejecuta Python y pytest SIEMPRE con `.venv/bin/python`, nunca `python` a secas.
- Un `ModuleNotFoundError` de pydantic, httpx o pytest-httpx significa que
  usaste el intérprete equivocado, **no** que falte la dependencia.
- Existe un `.env` con credenciales reales. No lo leas, no lo modifiques,
  no lo commitees. Tampoco pegues tracebacks que impriman `Settings`.

## Contratos
- `docs/01-CONTRATOS-DE-DATOS.md` (v2.4) es ley. No inventes campos,
  no renombres, no añadas "por comodidad".
- Si una tarea parece exigir cambiar un contrato: **detente y pregunta.**
  No lo cambies tú.
- Antes de empezar cualquier micro-tarea, lee `docs/00`, `docs/01`
  y `docs/05`.

## Método
- Se trabaja por micro-tareas definidas en `docs/PLAN-MIGRACION.md`.
  Una a la vez, en orden. No adelantes trabajo de la siguiente.
- Al terminar cada una: `.venv/bin/python -m pytest -q` y un commit
  con mensaje `MN: descripción`.
- **Si para que un test pase hay que cambiar una aserción de
  comportamiento existente, DETENTE y explica.** El criterio 11 de
  `docs/05` exige que la migración no cambie ninguna.
- No digas "todos los tests pasan": pega la línea final de pytest.

## Prohibido sin permiso explícito
- Ejecutar `scripts/cosecha.py` o `scripts/lote.py` sin `--dry-run`.
  Hacen peticiones reales a servidores universitarios.
- Tocar `data/`, `legisuni.db` o `fixtures/`.
- `git push`, `git reset --hard`, `git checkout` de archivos con cambios.
- Instalar dependencias nuevas.

## Idioma
Código, nombres y commits en español.