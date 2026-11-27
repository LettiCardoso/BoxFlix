"""
Configuração centralizada de logs do BoxFlix.

Padroniza o formato das mensagens de log enviadas para o console (stdout),
facilitando a leitura em desenvolvimento e a coleta por ferramentas de
observabilidade (como Elastic Stack / Docker logs) em produção.
"""

import logging


def configurar_logger(app):
    """Configura o logger da aplicação Flask com formato padronizado."""
    formato = logging.Formatter(
        "[%(asctime)s] %(levelname)s em %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formato)
        app.logger.addHandler(handler)
    else:
        for handler in app.logger.handlers:
            handler.setFormatter(formato)

    app.logger.setLevel(logging.INFO)
