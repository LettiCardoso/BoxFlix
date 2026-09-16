// modal.js — abre um modal com os detalhes do filme/série clicado.
// Funciona em qualquer página que tenha o elemento #modal-detalhe
// (dashboard e busca avançada). Delegação de evento: qualquer elemento
// com [data-filme-id] abre o modal ao ser clicado.

(function () {
  const modal = document.getElementById("modal-detalhe");
  if (!modal) return; // página sem modal, não faz nada

  const modalPoster = document.getElementById("modal-poster");
  const modalTipo = document.getElementById("modal-tipo");
  const modalTitulo = document.getElementById("modal-titulo");
  const modalMeta = document.getElementById("modal-meta");
  const modalDescricao = document.getElementById("modal-descricao");
  const btnFechar = document.getElementById("modal-fechar");

  async function abrirModal(id) {
    try {
      const resposta = await fetch(`/api/titulo/${id}`);

      if (resposta.status === 401 || resposta.redirected) {
        window.location.href = "/";
        return;
      }
      if (!resposta.ok) return;

      const item = await resposta.json();

      modalTitulo.textContent = item.titulo;
      modalTipo.textContent = item.tipo === "série" ? "SÉRIE" : "FILME";
      modalMeta.textContent = `${item.genero} · ${item.ano} · ★ ${item.nota} · Classificação ${item.classificacao}`;
      modalDescricao.textContent = item.descricao || "Sem descrição disponível.";
      modalPoster.style.backgroundImage = item.poster ? `url("${item.poster}")` : "none";

      modal.classList.add("modal--aberto");
      document.body.style.overflow = "hidden";
    } catch (erro) {
      console.error("Não foi possível carregar os detalhes:", erro);
    }
  }

  function fecharModal() {
    modal.classList.remove("modal--aberto");
    document.body.style.overflow = "";
  }

  document.addEventListener("click", (evento) => {
    const alvo = evento.target.closest("[data-filme-id]");
    if (alvo) {
      abrirModal(alvo.dataset.filmeId);
    }
  });

  btnFechar.addEventListener("click", fecharModal);
  modal.addEventListener("click", (evento) => {
    if (evento.target === modal) fecharModal(); // clique fora da caixa fecha
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") fecharModal();
  });
})();
