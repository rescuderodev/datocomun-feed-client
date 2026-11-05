from dataclasses import dataclass, field
from datetime import datetime


def _fecha(valor):
    return datetime.fromisoformat(valor) if valor else None


@dataclass
class Candidatura:
    siglas: str
    nombre: str
    escanos: int = 0
    votos: int | None = None
    pct: float | None = None

    @classmethod
    def from_dict(cls, d):
        return cls(
            siglas=d["siglas"],
            nombre=d.get("nombre", d["siglas"]),
            escanos=d.get("escanos", 0),
            votos=d.get("votos"),
            pct=d.get("pct"),
        )


@dataclass
class Avance:
    convocatoria: str
    camara: str
    tipo: str  # provisional | definitivo
    escrutado_pct: float
    escanos_total: int
    mayoria_absoluta: int
    candidaturas: list = field(default_factory=list)
    actualizado: datetime | None = None
    simulacro: bool = False

    @classmethod
    def from_dict(cls, d):
        return cls(
            convocatoria=d["convocatoria"],
            camara=d["camara"],
            tipo=d["tipo"],
            escrutado_pct=d["escrutado_pct"],
            escanos_total=d["escanos_total"],
            mayoria_absoluta=d["mayoria_absoluta"],
            candidaturas=[Candidatura.from_dict(c) for c in d.get("candidaturas", [])],
            actualizado=_fecha(d.get("actualizado")),
            simulacro=d.get("simulacro", False),
        )

    def lider(self):
        return max(self.candidaturas, key=lambda c: c.escanos, default=None)


@dataclass
class Circunscripcion:
    codigo: str
    nombre: str
    escanos_en_juego: int
    escanos_convocatoria_anterior: int
    escrutado_pct: float
    votos_validos: int
    blancos: int
    nulos: int
    candidaturas: list = field(default_factory=list)
    hora_local: str = "+01:00"
    actualizado: datetime | None = None

    @classmethod
    def from_dict(cls, d):
        candidaturas = [Candidatura.from_dict(c) for c in d.get("candidaturas", [])]
        # la API no garantiza el orden, las queremos de mas a menos votos
        candidaturas.sort(key=lambda c: c.votos or 0, reverse=True)
        return cls(
            codigo=d["circunscripcion"]["codigo"],
            nombre=d["circunscripcion"]["nombre"],
            escanos_en_juego=d["escanos_en_juego"],
            escanos_convocatoria_anterior=d.get("escanos_convocatoria_anterior", d["escanos_en_juego"]),
            escrutado_pct=d["escrutado_pct"],
            votos_validos=d["votos_validos"],
            blancos=d["blancos"],
            nulos=d["nulos"],
            candidaturas=candidaturas,
            hora_local=d.get("hora_local", "+01:00"),
            actualizado=_fecha(d.get("actualizado")),
        )

    @property
    def cambio_escanos(self):
        """Escaños de mas o de menos respecto a la convocatoria anterior (Madrid +1, Cadiz -1)."""
        return self.escanos_en_juego - self.escanos_convocatoria_anterior
