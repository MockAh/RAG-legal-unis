import sqlite3
from datetime import datetime
from pathlib import Path

from legisuni.contracts import DownloadResult, IntentoPuerta
from legisuni.descargador.store import Store


def _resultado_exitoso(**overrides) -> DownloadResult:
    datos = dict(
        encargo_id="uam:reglamento-organico",
        modo="juridico",
        exito=True,
        ruta_local=Path("/datos/uam/reglamento-organico__2026-01-01.pdf"),
        sha256="a" * 64,
        bytes=1234,
        content_type="application/pdf",
        http_status=200,
        capturado_en=datetime(2026, 1, 1, 12, 0, 0),
        url_final="http://example.org/doc.pdf",
        intentos=[],
    )
    datos.update(overrides)
    return DownloadResult(**datos)


def test_crear_store_crea_archivo_y_tabla_vacia(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Store(db_path) as store:
        assert db_path.exists()
        assert store.contar() == 0


def test_guardar_exitoso_y_recuperar_hash(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar_descarga(resultado, grupo_alias="g1")
        assert store.hash_registrado(resultado.encargo_id) == resultado.sha256


def test_guardar_dos_veces_mismo_entry_id_no_duplica(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        store.guardar(resultado)
        assert store.contar() == 1


def test_guardar_mismo_entry_id_con_datos_distintos_actualiza(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        store.guardar_descarga(resultado, grupo_alias="g1")
        actualizado = resultado.model_copy(update={"sha256": "b" * 64})
        store.guardar(actualizado)
        store.guardar_descarga(actualizado, grupo_alias="g1")
        assert store.contar() == 1
        assert store.hash_registrado(resultado.encargo_id) == "b" * 64


def test_hash_registrado_entry_id_inexistente_devuelve_none(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        assert store.hash_registrado("uam:no-existe") is None


def test_hash_registrado_con_exito_falso_devuelve_none(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso(exito=False, sha256="c" * 64)
        store.guardar_descarga(resultado, grupo_alias="g1")
        assert store.hash_registrado(resultado.encargo_id) is None


def test_ruta_registrada_vuelve_como_path(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar_descarga(resultado, grupo_alias="g1")
        ruta = store.ruta_registrada(resultado.encargo_id)
        assert isinstance(ruta, Path)
        assert ruta == resultado.ruta_local


def test_tipos_en_disco_son_texto_no_blob(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Store(db_path) as store:
        store.guardar(_resultado_exitoso())

    conn = sqlite3.connect(str(db_path))
    fila = conn.execute(
        "SELECT typeof(ruta_local) AS t_ruta, typeof(capturado_en) AS t_capturado "
        "FROM documentos"
    ).fetchone()
    conn.close()
    assert fila[0] == "text"
    assert fila[1] == "text"


def test_utf8_se_conserva_intacto(tmp_path: Path) -> None:
    entry_id = "uñam:reglamento-académico"
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso(encargo_id=entry_id)
        store.guardar_descarga(resultado, grupo_alias="g1")
        assert store.hash_registrado(entry_id) == resultado.sha256


def test_guardar_resultado_fallido_sin_excepcion(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = DownloadResult(
            encargo_id="uam:url-muerta",
            modo="juridico",
            exito=False,
            motivo_fallo="url_muerta",
            capturado_en=datetime(2026, 1, 1),
            intentos=[],
        )
        store.guardar(resultado)
        assert store.contar() == 1


def test_base_nueva_tiene_las_tablas_descargas_e_intentos(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Store(db_path):
        pass

    conn = sqlite3.connect(str(db_path))
    tablas = {
        fila[0]
        for fila in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    conn.close()
    assert {"documentos", "descargas", "intentos"} <= tablas


def test_guardar_descarga_escribe_en_descargas_y_registra_grupo_alias(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar_descarga(resultado, grupo_alias="uam:reglamento-organico")

        conn = store._conn
        fila = conn.execute(
            "SELECT grupo_alias, sha256 FROM descargas WHERE encargo_id = ?",
            (resultado.encargo_id,),
        ).fetchone()
        assert fila["grupo_alias"] == "uam:reglamento-organico"
        assert fila["sha256"] == resultado.sha256


def test_guardar_descarga_con_hash_nuevo_conserva_ambas_filas(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar_descarga(resultado, grupo_alias="g1")

        version_nueva = resultado.model_copy(update={"sha256": "b" * 64})
        store.guardar_descarga(version_nueva, grupo_alias="g1")

        filas = store._conn.execute(
            "SELECT sha256 FROM descargas WHERE encargo_id = ? ORDER BY sha256",
            (resultado.encargo_id,),
        ).fetchall()
        assert {fila["sha256"] for fila in filas} == {resultado.sha256, "b" * 64}


def test_guardar_descarga_misma_clave_actualiza_sin_duplicar(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar_descarga(resultado, grupo_alias="g1")
        store.guardar_descarga(resultado, grupo_alias="g1")

        filas = store._conn.execute(
            "SELECT COUNT(*) AS n FROM descargas WHERE encargo_id = ?",
            (resultado.encargo_id,),
        ).fetchone()
        assert filas["n"] == 1


def test_guardar_descarga_escribe_un_intento_por_puerta_pedida(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso(
            intentos=[
                IntentoPuerta(
                    orden=0,
                    url="http://example.org/doc.pdf",
                    url_pedida="http://example.org/doc.pdf",
                    url_final="http://example.org/doc.pdf",
                    enlace_vestibulo=None,
                    http_status=200,
                    exito=True,
                    motivo_fallo=None,
                )
            ]
        )
        store.guardar_descarga(resultado, grupo_alias="g1")

        filas = store._conn.execute(
            "SELECT encargo_id, orden, http_status FROM intentos WHERE encargo_id = ?",
            (resultado.encargo_id,),
        ).fetchall()
        assert len(filas) == 1
        assert filas[0]["orden"] == 0
        assert filas[0]["http_status"] == 200


def test_guardar_descarga_no_afecta_la_tabla_documentos(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar_descarga(resultado, grupo_alias="g1")
        assert store.contar() == 0


def test_cerrar_y_reabrir_conserva_filas(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    store = Store(db_path)
    store.guardar(_resultado_exitoso())
    store.cerrar()

    with Store(db_path) as reabierto:
        assert reabierto.contar() == 1


# M29: alias_por_hash (docs/05 criterio 16). Solo descargas exitosas, dueñas de su
# archivo (duplicado_de IS NULL), del mismo grupo_alias y de otro encargo_id.

_GRUPO = "uam:reglamento-organico"


def test_alias_por_hash_encuentra_el_original_del_mismo_grupo(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        original = _resultado_exitoso(encargo_id="uam:ro:aaaaaaaaaaaa")
        store.guardar_descarga(original, _GRUPO)

        assert store.alias_por_hash(_GRUPO, "a" * 64, "uam:ro:bbbbbbbbbbbb") == (
            "uam:ro:aaaaaaaaaaaa",
            original.ruta_local,
        )


def test_alias_por_hash_no_cruza_grupos(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        store.guardar_descarga(_resultado_exitoso(encargo_id="uam:ro:aaaaaaaaaaaa"), _GRUPO)

        assert store.alias_por_hash("uam:otro-reglamento", "a" * 64, "uam:ro:bbbbbbbbbbbb") is None


def test_alias_por_hash_ignora_descargas_fallidas(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        fallida = _resultado_exitoso(encargo_id="uam:ro:aaaaaaaaaaaa", exito=False, motivo_fallo="http_error")
        store.guardar_descarga(fallida, _GRUPO)

        assert store.alias_por_hash(_GRUPO, "a" * 64, "uam:ro:bbbbbbbbbbbb") is None


def test_alias_por_hash_no_es_alias_de_si_mismo(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        store.guardar_descarga(_resultado_exitoso(encargo_id="uam:ro:aaaaaaaaaaaa"), _GRUPO)

        assert store.alias_por_hash(_GRUPO, "a" * 64, "uam:ro:aaaaaaaaaaaa") is None


def test_alias_por_hash_nunca_elige_un_alias_como_original(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        # solo queda registrado un alias (su original es de otro grupo o ya no está en la base)
        alias = _resultado_exitoso(encargo_id="uam:ro:bbbbbbbbbbbb", duplicado_de="uam:ro:aaaaaaaaaaaa")
        store.guardar_descarga(alias, _GRUPO)

        assert store.alias_por_hash(_GRUPO, "a" * 64, "uam:ro:cccccccccccc") is None


# M34: hash_registrado y ruta_registrada leen `descargas`, la última fila escrita del
# encargo (capturado_en DESC, rowid DESC), y solo si es exitosa. La última escritura
# gana, como en `documentos`.


def _fallo(**overrides) -> DownloadResult:
    datos = dict(
        encargo_id="uam:reglamento-organico",
        modo="juridico",
        exito=False,
        motivo_fallo="timeout",
        capturado_en=datetime(2026, 1, 1, 12, 0, 0),
        intentos=[],
    )
    datos.update(overrides)
    return DownloadResult(**datos)


def test_fallo_viejo_y_exito_posterior_da_el_exito(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        store.guardar_descarga(_fallo(capturado_en=datetime(2026, 1, 1)), "g1")
        exito = _resultado_exitoso(capturado_en=datetime(2026, 1, 2))
        store.guardar_descarga(exito, "g1")
        assert store.hash_registrado(exito.encargo_id) == exito.sha256
        assert store.ruta_registrada(exito.encargo_id) == exito.ruta_local


def test_exito_y_fallo_posterior_da_none(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        exito = _resultado_exitoso(capturado_en=datetime(2026, 1, 1))
        store.guardar_descarga(exito, "g1")
        store.guardar_descarga(_fallo(capturado_en=datetime(2026, 1, 2)), "g1")
        assert store.hash_registrado(exito.encargo_id) is None
        assert store.ruta_registrada(exito.encargo_id) is None


def test_solo_fallos_con_sha256_nulo_da_none(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        store.guardar_descarga(_fallo(capturado_en=datetime(2026, 1, 1)), "g1")
        store.guardar_descarga(_fallo(capturado_en=datetime(2026, 1, 2)), "g1")
        assert store.hash_registrado("uam:reglamento-organico") is None
        assert store.ruta_registrada("uam:reglamento-organico") is None


def test_dos_versiones_hash_y_ruta_salen_de_la_misma_fila(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        store.guardar_descarga(
            _resultado_exitoso(sha256="a" * 64, ruta_local=Path("/datos/a.pdf"), capturado_en=datetime(2026, 1, 1)),
            "g1",
        )
        store.guardar_descarga(
            _resultado_exitoso(sha256="b" * 64, ruta_local=Path("/datos/b.pdf"), capturado_en=datetime(2026, 1, 2)),
            "g1",
        )
        assert store.hash_registrado("uam:reglamento-organico") == "b" * 64
        assert store.ruta_registrada("uam:reglamento-organico") == Path("/datos/b.pdf")


def test_capturado_en_decide_antes_que_rowid(tmp_path: Path) -> None:
    # el upsert de un hash ya registrado conserva su rowid viejo
    with Store(tmp_path / "test.db") as store:
        version_a = _resultado_exitoso(sha256="a" * 64, ruta_local=Path("/datos/a.pdf"), capturado_en=datetime(2026, 1, 1))
        store.guardar_descarga(version_a, "g1")
        store.guardar_descarga(
            _resultado_exitoso(sha256="b" * 64, ruta_local=Path("/datos/b.pdf"), capturado_en=datetime(2026, 1, 2)),
            "g1",
        )
        store.guardar_descarga(version_a.model_copy(update={"capturado_en": datetime(2026, 1, 3)}), "g1")
        assert store.hash_registrado("uam:reglamento-organico") == "a" * 64
        assert store.ruta_registrada("uam:reglamento-organico") == Path("/datos/a.pdf")


def test_fila_solo_en_documentos_ya_no_cuenta(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        assert store.hash_registrado(resultado.encargo_id) is None
        assert store.ruta_registrada(resultado.encargo_id) is None
