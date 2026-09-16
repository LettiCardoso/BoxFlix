// Busca Avançada — segue o mesmo padrão de fetch do home.js:
// consulta /api/buscar (protegida por login no Flask) e redesenha a grade.

const campoBusca = document.getElementById("campoBusca");
const anoMin = document.getElementById("anoMin");
const anoMax = document.getElementById("anoMax");
const anoMinLabel = document.getElementById("anoMinLabel");
const anoMaxLabel = document.getElementById("anoMaxLabel");
const notaMin = document.getElementById("notaMin");
const notaLabel = document.getElementById("notaLabel");
const grupoClassificacao = document.getElementById("grupoClassificacao");
const btnAplicar = document.getElementById("btnAplicar");
const btnLimpar = document.getElementById("btnLimpar");
const gradeFilmes = document.getElementById("gradeFilmes");
const semResultados = document.getElementById("semResultados");
const contadorResultados = document.getElementById("contadorResultados");

let classificacoesAtivas = [];
let temporizadorBusca = null;

// Impede que o <form> da barra de busca do topo recarregue a página
campoBusca.closest("form").addEventListener("submit", (e) => e.preventDefault());

// --- Chips de classificação ---
grupoClassificacao.querySelectorAll(".busca-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    chip.classList.toggle("busca-chip--ativo");
    const valor = chip.dataset.valor;
    if (chip.classList.contains("busca-chip--ativo")) {
      classificacoesAtivas.push(valor);
    } else {
      classificacoesAtivas = classificacoesAtivas.filter((v) => v !== valor);
    }
    buscar();
  });
});

// --- Labels dos sliders em tempo real ---
anoMin.addEventListener("input", () => (anoMinLabel.textContent = anoMin.value));
anoMax.addEventListener("input", () => (anoMaxLabel.textContent = anoMax.value));
notaMin.addEventListener("input", () => (notaLabel.textContent = notaMin.value));

function montaParametros() {
  const params = new URLSearchParams();
  params.set("q", campoBusca.value.trim());
  params.set("ano_min", anoMin.value);
  params.set("ano_max", anoMax.value);
  params.set("nota_min", notaMin.value);

  classificacoesAtivas.forEach((c) => params.append("classificacao", c));

  document.querySelectorAll('.busca-checkbox input[type="checkbox"]:checked').forEach((cb) => {
    params.append("qualidade", cb.value);
  });

  return params;
}

async function buscar() {
  const params = montaParametros();

  try {
    const resposta = await fetch(`/api/buscar?${params.toString()}`);

    if (resposta.status === 401 || resposta.redirected) {
      window.location.href = "/";
      return;
    }

    const dados = await resposta.json();
    renderizaFilmes(dados.filmes);
    contadorResultados.textContent = `Exibindo ${dados.total} resultados encontrados`;
  } catch (erro) {
    console.error("Erro ao buscar filmes:", erro);
  }
}

function renderizaFilmes(filmes) {
  gradeFilmes.innerHTML = "";

  if (filmes.length === 0) {
    semResultados.style.display = "block";
    return;
  }
  semResultados.style.display = "none";

  filmes.forEach((filme) => {
    const badge4k = filme.qualidade.includes("4K HDR")
      ? '<span class="busca-badge busca-badge--4k">4K</span>'
      : "<span></span>";

    const card = document.createElement("div");
    card.className = "busca-card";
    card.dataset.filmeId = filme.id;
    card.style.backgroundImage = `url("${filme.poster}")`;
    card.innerHTML = `
      <div class="busca-card__badges">
        ${badge4k}
        <span class="busca-badge busca-badge--nota">★ ${filme.nota}</span>
      </div>
      <div class="busca-card__info">
        <p class="busca-card__titulo">${filme.titulo}</p>
        <span class="busca-card__meta">${filme.genero} · ${filme.ano}</span>
      </div>
    `;
    gradeFilmes.appendChild(card);
  });
}

// --- Busca ao vivo enquanto digita (debounce de 300ms) ---
campoBusca.addEventListener("input", () => {
  clearTimeout(temporizadorBusca);
  temporizadorBusca = setTimeout(buscar, 300);
});

btnAplicar.addEventListener("click", buscar);

btnLimpar.addEventListener("click", () => {
  campoBusca.value = "";
  anoMin.value = 1980; anoMinLabel.textContent = 1980;
  anoMax.value = 2026; anoMaxLabel.textContent = 2026;
  notaMin.value = 0; notaLabel.textContent = 0;
  classificacoesAtivas = [];
  grupoClassificacao.querySelectorAll(".busca-chip").forEach((c) => c.classList.remove("busca-chip--ativo"));
  document.querySelectorAll('.busca-checkbox input[type="checkbox"]').forEach((cb) => (cb.checked = true));
  buscar();
});

document.addEventListener("DOMContentLoaded", buscar);
