// CineFlix — front-end
// Busca o conteúdo em /api/content (Flask) e monta a home.
// Cada cartão sem "poster" definido vira um espaço reservado pronto para
// receber a arte do filme/série depois.

async function loadContent() {
  try {
    const res = await fetch('/api/content');
    const data = await res.json();

    renderHero(data.destaque);
    renderGrid('grid-populares', data.populares, 'filme');
    renderGrid('grid-series', data.series_em_alta, 'série');
  } catch (err) {
    console.error('Não foi possível carregar o conteúdo:', err);
  }
}

function renderHero(destaque) {
  if (!destaque) return;

  document.getElementById('hero-tipo').textContent = destaque.tipo;
  document.getElementById('hero-tag').textContent = destaque.tag;
  document.getElementById('hero-titulo').textContent = destaque.titulo;
  document.getElementById('hero-desc').textContent = destaque.descricao;

  const bg = document.getElementById('hero-bg');
  if (destaque.poster) {
    bg.style.backgroundImage = `url("${destaque.poster}")`;
  }
}

function renderGrid(containerId, items, kind) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'card';

    if (item.poster) {
      card.style.backgroundImage = `url("${item.poster}")`;
    } else {
      // Espaço reservado: aqui entra o pôster do filme/série.
      card.innerHTML = `
        <div class="card__placeholder">
          <svg viewBox="0 0 24 24" class="icon">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <circle cx="9" cy="9" r="2"/>
            <path d="M21 15l-5-5L5 21"/>
          </svg>
          <span>Adicionar ${kind}</span>
        </div>`;
    }

    if (item.titulo) {
      const label = document.createElement('div');
      label.className = 'card__label';
      label.textContent = item.titulo;
      card.appendChild(label);
    }

    container.appendChild(card);
  });
}

document.addEventListener('DOMContentLoaded', loadContent);
