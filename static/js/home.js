// Home (área logada) — busca o conteúdo em /api/content (protegido por
// login no Flask) e monta o herói + os cartões de filme/série.
// O menu do topo troca entre 4 "views" na mesma página, usando o hash da URL:
//   #inicio (padrão) · #filmes · #series · #minha-lista
// Cartões sem "poster" definido viram um espaço reservado.

let catalogo = []; // catálogo completo (vem de /api/buscar), usado por Filmes/Séries/Minha Lista
let destaqueId = null; // id do slide que está aparecendo no hero

// Carrossel do hero
const INTERVALO_HERO = 7000; // ms entre slides
const reduzMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let slides = [];
let slideAtual = 0;
let timerAutoplay = null;
let timerTroca = null;
let heroComMouse = false;

/* ------------------------------------------------------------------
   Minha Lista — guardada no localStorage do navegador (uma lista por
   usuário logado). Para sincronizar entre aparelhos seria preciso uma
   tabela no banco + rotas na API.
------------------------------------------------------------------- */
function chaveLista() {
  const avatar = document.querySelector(".home-avatar");
  const nome = (avatar && avatar.title) || "anonimo";
  return `boxflix:minha-lista:${nome}`;
}

function lerLista() {
  try {
    const dados = JSON.parse(localStorage.getItem(chaveLista()) || "[]");
    return Array.isArray(dados) ? dados.map(Number) : [];
  } catch (erro) {
    return [];
  }
}

function salvarLista(ids) {
  try {
    localStorage.setItem(chaveLista(), JSON.stringify(ids));
  } catch (erro) {
    console.error("Não foi possível salvar a Minha Lista:", erro);
  }
}

function estaNaLista(id) {
  return lerLista().includes(Number(id));
}

// adiciona/remove e devolve true se o item passou a estar na lista
function alternarLista(id) {
  id = Number(id);
  let ids = lerLista();
  if (ids.includes(id)) {
    ids = ids.filter((x) => x !== id);
  } else {
    ids.push(id);
  }
  salvarLista(ids);
  return ids.includes(id);
}

const ICONE_MAIS = '<svg viewBox="0 0 24 24" class="icon"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
const ICONE_CHECK = '<svg viewBox="0 0 24 24" class="icon"><polyline points="20 6 9 17 4 12"/></svg>';

function atualizarBotaoCard(botao, ativo) {
  botao.classList.toggle("card__lista--ativo", ativo);
  botao.setAttribute("aria-pressed", String(ativo));
  botao.title = ativo ? "Remover da Minha Lista" : "Adicionar à Minha Lista";
  botao.setAttribute("aria-label", botao.title);
  botao.innerHTML = ativo ? ICONE_CHECK : ICONE_MAIS;
}

function atualizarBotaoHero() {
  const botao = document.getElementById("hero-lista");
  if (!botao) return;
  if (destaqueId === null) {
    botao.hidden = true;
    return;
  }
  const ativo = estaNaLista(destaqueId);
  botao.innerHTML = (ativo ? ICONE_CHECK : ICONE_MAIS).replace("class=\"icon\"", "class=\"icon icon--sm\"")
    + (ativo ? " Na Minha Lista" : " Minha Lista");
}

// mantém todos os botões da página coerentes com a lista salva
function sincronizarBotoes() {
  document.querySelectorAll(".card__lista").forEach((botao) => {
    atualizarBotaoCard(botao, estaNaLista(botao.dataset.listaId));
  });
  atualizarBotaoHero();
}

/* ------------------------------------------------------------------
   Carregamento
------------------------------------------------------------------- */
async function buscarJson(url) {
  const resposta = await fetch(url);
  if (resposta.status === 401 || resposta.redirected) {
    // sessão expirada -> volta pro login
    window.location.href = "/";
    return null;
  }
  return resposta.json();
}

async function carregarConteudo() {
  try {
    const [dados, busca] = await Promise.all([
      buscarJson("/api/content"),
      buscarJson("/api/buscar"),
    ]);
    if (!dados) return;

    catalogo = busca ? busca.filmes : [];

    iniciarCarrossel(montarSlides(dados.destaque, catalogo));
    renderizarGrid("grid-populares", dados.populares, "filme");
    renderizarGrid("grid-series", dados.series_em_alta, "série");
    mostrarView();
  } catch (erro) {
    console.error("Não foi possível carregar o conteúdo:", erro);
  }
}

/* ------------------------------------------------------------------
   Hero em carrossel: o destaque da semana + os títulos mais bem
   avaliados do catálogo. Passa sozinho; pausa com o mouse em cima,
   com o modal aberto, em outra aba ou fora da aba Início.
------------------------------------------------------------------- */
function montarSlides(destaque, itens) {
  const lista = [];

  if (destaque) {
    lista.push({
      id: destaque.id,
      tipo: String(destaque.tipo).toUpperCase(),
      tag: destaque.tag,
      titulo: destaque.titulo,
      descricao: destaque.descricao,
      poster: destaque.poster,
    });
  }

  itens
    .filter((i) => !destaque || i.id !== destaque.id)
    .sort((a, b) => b.nota - a.nota)
    .slice(0, 4)
    .forEach((i) => {
      lista.push({
        id: i.id,
        tipo: String(i.tipo).toUpperCase(),
        tag: `Em alta · ★ ${i.nota}`,
        titulo: i.titulo,
        descricao: i.descricao,
        poster: i.poster,
      });
    });

  return lista;
}

// Escreve os dados de um slide no hero
function aplicarSlide(slide) {
  document.getElementById("hero-tipo").textContent = slide.tipo;
  document.getElementById("hero-tag").textContent = slide.tag;
  document.getElementById("hero-titulo").textContent = slide.titulo;
  document.getElementById("hero-desc").textContent = slide.descricao || "";

  // O pôster vira uma variável CSS: o home.css usa ela para o fundo
  // desfocado e para o pôster nítido ao lado (evita esticar a imagem).
  const hero = document.getElementById("hero");
  if (slide.poster) {
    hero.style.setProperty("--hero-img", `url("${slide.poster}")`);
    hero.classList.add("hero--com-poster");
  } else {
    hero.style.removeProperty("--hero-img");
    hero.classList.remove("hero--com-poster");
  }

  const botaoInfo = document.getElementById("hero-mais-info");
  if (botaoInfo && slide.id) {
    botaoInfo.dataset.filmeId = slide.id;
  }

  destaqueId = slide.id || null;
  atualizarBotaoHero();
}

function atualizarBolinhas() {
  document.querySelectorAll(".hero__dot").forEach((dot, i) => {
    const ativo = i === slideAtual;
    dot.classList.toggle("hero__dot--ativo", ativo);
    dot.setAttribute("aria-current", String(ativo));
  });
}

function irParaSlide(indice, animar = true) {
  if (slides.length === 0) return;
  indice = (indice + slides.length) % slides.length;
  slideAtual = indice;
  atualizarBolinhas();

  const hero = document.getElementById("hero");
  const trocar = () => {
    aplicarSlide(slides[indice]);
    hero.classList.remove("hero--trocando");
  };

  clearTimeout(timerTroca);
  if (!animar || reduzMovimento) {
    trocar();
    return;
  }
  hero.classList.add("hero--trocando"); // some...
  timerTroca = setTimeout(trocar, 350); // ...troca o conteúdo e reaparece
}

function reiniciarAutoplay() {
  clearInterval(timerAutoplay);
  if (slides.length < 2 || reduzMovimento) return;

  timerAutoplay = setInterval(() => {
    const modal = document.getElementById("modal-detalhe");
    const modalAberto = modal && modal.classList.contains("modal--aberto");
    if (heroComMouse || modalAberto || document.hidden || document.getElementById("hero").hidden) return;
    irParaSlide(slideAtual + 1);
  }, INTERVALO_HERO);
}

function iniciarCarrossel(lista) {
  slides = lista;
  if (slides.length === 0) return;

  // carrega os pôsteres antes, para a troca não "piscar"
  slides.forEach((slide) => {
    if (slide.poster) new Image().src = slide.poster;
  });

  const hero = document.getElementById("hero");
  const nav = document.getElementById("hero-nav");
  const dots = document.getElementById("hero-dots");

  dots.innerHTML = "";
  slides.forEach((slide, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "hero__dot";
    dot.setAttribute("aria-label", `Ver ${slide.titulo}`);
    dot.addEventListener("click", () => {
      irParaSlide(i);
      reiniciarAutoplay();
    });
    dots.appendChild(dot);
  });

  document.getElementById("hero-prev").onclick = () => {
    irParaSlide(slideAtual - 1);
    reiniciarAutoplay();
  };
  document.getElementById("hero-next").onclick = () => {
    irParaSlide(slideAtual + 1);
    reiniciarAutoplay();
  };
  nav.hidden = slides.length < 2;

  hero.addEventListener("mouseenter", () => (heroComMouse = true));
  hero.addEventListener("mouseleave", () => (heroComMouse = false));

  const botaoLista = document.getElementById("hero-lista");
  if (botaoLista) {
    botaoLista.onclick = () => {
      if (destaqueId === null) return;
      alternarLista(destaqueId);
      sincronizarBotoes();
      if (viewAtual() === "minha-lista") renderizarCatalogo("minha-lista");
    };
  }

  irParaSlide(0, false);
  reiniciarAutoplay();
}

function renderizarGrid(idContainer, itens, tipo) {
  const container = document.getElementById(idContainer);
  container.innerHTML = "";

  itens.forEach((item) => {
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.filmeId = item.id;

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

    if (item.id) {
      const botao = document.createElement("button");
      botao.type = "button";
      botao.className = "card__lista";
      botao.dataset.listaId = item.id;
      atualizarBotaoCard(botao, estaNaLista(item.id));
      botao.addEventListener("click", (evento) => {
        evento.stopPropagation(); // não abre o modal de detalhes
        alternarLista(item.id);
        sincronizarBotoes();
        if (viewAtual() === "minha-lista") renderizarCatalogo("minha-lista");
      });
      card.appendChild(botao);
    }

    container.appendChild(card);
  });
}

/* ------------------------------------------------------------------
   Views (Início / Filmes / Séries / Minha Lista)
------------------------------------------------------------------- */
const VIEWS = ["inicio", "filmes", "series", "minha-lista"];

function viewAtual() {
  const nome = window.location.hash.replace("#", "");
  return VIEWS.includes(nome) ? nome : "inicio";
}

function renderizarCatalogo(view) {
  let itens;
  let titulo;
  let vazio = "";

  if (view === "filmes") {
    titulo = "Filmes";
    itens = catalogo.filter((i) => i.tipo === "filme");
  } else if (view === "series") {
    titulo = "Séries";
    itens = catalogo.filter((i) => i.tipo === "série");
  } else {
    titulo = "Minha Lista";
    // mantém a ordem em que o usuário foi adicionando
    itens = lerLista()
      .map((id) => catalogo.find((i) => i.id === id))
      .filter(Boolean);
    vazio = "Sua lista está vazia. Passe o mouse sobre um filme ou série e clique no + para adicionar aqui.";
  }

  document.getElementById("catalogo-titulo").textContent = titulo;
  renderizarGrid("grid-catalogo", itens, view === "series" ? "série" : "filme");

  const msg = document.getElementById("catalogo-vazio");
  msg.textContent = itens.length === 0 ? (vazio || "Nenhum título encontrado.") : "";
  msg.hidden = itens.length === 0;
}

function mostrarView() {
  const view = viewAtual();
  const inicio = view === "inicio";

  document.getElementById("hero").hidden = !inicio;
  document.getElementById("row-populares").hidden = !inicio;
  document.getElementById("row-series").hidden = !inicio;
  document.getElementById("view-catalogo").hidden = inicio;

  document.querySelectorAll(".home-nav__link").forEach((link) => {
    link.classList.toggle("home-nav__link--active", link.dataset.view === view);
  });

  if (!inicio) renderizarCatalogo(view);
  sincronizarBotoes();
}

window.addEventListener("hashchange", () => {
  mostrarView();
  window.scrollTo(0, 0);
});

document.addEventListener("DOMContentLoaded", carregarConteudo);
