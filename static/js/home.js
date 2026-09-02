// Home (área logada) — busca o conteúdo em /api/content (protegido por
// login no Flask) e monta o herói + os cartões de filme/série.
// Cartões sem "poster" definido viram um espaço reservado.

async function carregarConteudo() {
  try {
    const resposta = await fetch("/api/content");

    if (resposta.status === 401 || resposta.redirected) {
      // sessão expirada -> volta pro login
      window.location.href = "/";
      return;
    }

    const dados = await resposta.json();
    renderizarHero(dados.destaque);
    renderizarGrid("grid-populares", dados.populares, "filme");
    renderizarGrid("grid-series", dados.series_em_alta, "série");
  } catch (erro) {
    console.error("Não foi possível carregar o conteúdo:", erro);
  }
}

function renderizarHero(destaque) {
  if (!destaque) return;

  document.getElementById("hero-tipo").textContent = destaque.tipo;
  document.getElementById("hero-tag").textContent = destaque.tag;
  document.getElementById("hero-titulo").textContent = destaque.titulo;
  document.getElementById("hero-desc").textContent = destaque.descricao;

  const bg = document.getElementById("hero-bg");
  if (destaque.poster) {
    bg.style.backgroundImage = `url("${destaque.poster}")`;
  }
}

function renderizarGrid(idContainer, itens, tipo) {
  const container = document.getElementById(idContainer);
  container.innerHTML = "";

  itens.forEach((item) => {
    const card = document.createElement("div");
    card.className = "card";

    if (item.poster) {
      card.style.backgroundImage = `url("${item.poster}")`;
    } else {
      card.innerHTML = `
        <div class="card__placeholder">
          <svg viewBox="0 0 24 24" class="icon">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <circle cx="9" cy="9" r="2"/>
            <path d="M21 15l-5-5L5 21"/>
          </svg>
          <span>Adicionar ${tipo}</span>
        </div>`;
    }

    if (item.titulo) {
      const label = document.createElement("div");
      label.className = "card__label";
      label.textContent = item.titulo;
      card.appendChild(label);
    }

    container.appendChild(card);
  });
}

document.addEventListener("DOMContentLoaded", carregarConteudo);
