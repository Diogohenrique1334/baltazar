from pathlib import Path
from typing import Sequence, Optional, Dict, Any, List, Union, Iterable
import shutil

def ultimo_arquivo(
    caminho: Union[str, Path],
    formato: Optional[Union[str, Iterable[str]]] = None,
    incluir_subpastas: bool = False,
    por: str = "mtime",  # "mtime" (modificação), "ctime" (criação*), "atime" (acesso)
) -> Optional[Path]:
    """
    Retorna o caminho completo do arquivo mais recente em `caminho`.
    - Se `formato` for None: considera todos os arquivos.
    - Se `formato` for str ou iterável de str: filtra por extensões (case-insensitive).
    Aceita com ou sem ponto: "csv" ou ".csv", ["csv", "txt"] etc.
    - `incluir_subpastas`: se True, busca recursivamente.
    - `por`: campo de tempo para ordenação (st_mtime | st_ctime | st_atime).
    *Observação*: em muitos sistemas, `ctime` não é "creation time" real; no Windows, sim.
    Retorna `None` se não houver arquivos que satisfaçam o filtro.
    """

    p = Path(caminho)

    # Monta o gerador de arquivos (somente arquivos, sem diretórios)
    it = p.rglob("*") if incluir_subpastas else p.iterdir()
    arquivos = (fp for fp in it if fp.is_file())

    # Normaliza formatos (extensões)
    if formato is None:
        candidatos = arquivos
    else:
        if isinstance(formato, (str, bytes)):
            formatos = {f".{formato.lstrip('.').lower()}"}
        else:
            formatos = {f".{ext.lstrip('.').lower()}" for ext in formato}

        def tem_ext_ok(fp: Path) -> bool:
            return fp.suffix.lower() in formatos

        candidatos = (fp for fp in arquivos if tem_ext_ok(fp))

    # Define a chave temporal
    if por == "mtime":
        keyfn = lambda fp: fp.stat().st_mtime
    elif por == "ctime":
        keyfn = lambda fp: fp.stat().st_ctime
    elif por == "atime":
        keyfn = lambda fp: fp.stat().st_atime
    else:
        raise ValueError("Parâmetro 'por' deve ser 'mtime', 'ctime' ou 'atime'.")

    # Seleciona o mais recente, com default=None para evitar ValueError
    mais_recente = max(candidatos, key=keyfn, default=None)
    return mais_recente


def mover_arquivo(caminho_origem: str, caminho_destino: str):
        """
        Move um arquivo de um caminho para outro.

        Parameters
        ----------
        caminho_origem : str
            Caminho completo do arquivo atual.
        caminho_destino : str
            Caminho completo onde o arquivo deve ser movido (incluindo o novo nome, se quiser).

        Exemplo:
            mover_arquivo("C:/entrada/arquivo.xlsx", "C:/saida/arquivo.xlsx")
        """
        origem = Path(caminho_origem)
        destino = Path(caminho_destino)

        # Garante que a pasta destino exista
        destino.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(origem), str(destino))
        print(f"Arquivo movido com sucesso para: {destino}")