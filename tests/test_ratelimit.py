from legisuni.descargador.ratelimit import RateLimiter


class RelojFalso:
    def __init__(self, inicio: float = 0.0) -> None:
        self.ahora = inicio

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


class DormirFalso:
    def __init__(self) -> None:
        self.llamadas: list[float] = []

    def __call__(self, segundos: float) -> None:
        self.llamadas.append(segundos)


def test_primera_peticion_a_un_host_no_duerme() -> None:
    reloj = RelojFalso()
    dormir = DormirFalso()
    limitador = RateLimiter(min_intervalo_s=1.0, reloj=reloj, dormir=dormir)

    assert limitador.esperar("https://a.mx/x") == 0.0
    assert dormir.llamadas == []


def test_segunda_peticion_inmediata_al_mismo_host_duerme_el_intervalo() -> None:
    reloj = RelojFalso()
    dormir = DormirFalso()
    limitador = RateLimiter(min_intervalo_s=1.0, reloj=reloj, dormir=dormir)

    limitador.esperar("https://a.mx/x")
    espera = limitador.esperar("https://a.mx/y")

    assert espera == 1.0
    assert dormir.llamadas == [1.0]


def test_segunda_peticion_a_host_distinto_no_duerme() -> None:
    reloj = RelojFalso()
    dormir = DormirFalso()
    limitador = RateLimiter(min_intervalo_s=1.0, reloj=reloj, dormir=dormir)

    limitador.esperar("https://a.mx/x")
    espera = limitador.esperar("https://b.mx/x")

    assert espera == 0.0
    assert dormir.llamadas == []


def test_segunda_peticion_tras_pasar_el_intervalo_no_duerme() -> None:
    reloj = RelojFalso()
    dormir = DormirFalso()
    limitador = RateLimiter(min_intervalo_s=1.0, reloj=reloj, dormir=dormir)

    limitador.esperar("https://a.mx/x")
    reloj.avanzar(2.0)
    espera = limitador.esperar("https://a.mx/y")

    assert espera == 0.0
    assert dormir.llamadas == []


def test_rutas_distintas_del_mismo_host_comparten_el_limite() -> None:
    reloj = RelojFalso()
    dormir = DormirFalso()
    limitador = RateLimiter(min_intervalo_s=1.0, reloj=reloj, dormir=dormir)

    limitador.esperar("https://a.mx/uno")
    espera = limitador.esperar("https://a.mx/dos")

    assert espera == 1.0
    assert dormir.llamadas == [1.0]
