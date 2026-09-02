// Lógica da tela de login: valida os campos no navegador
// e envia os dados para o backend Flask via fetch (API REST).

const form = document.getElementById("form-login");
const campoEmail = document.getElementById("email");
const campoSenha = document.getElementById("senha");
const btnEntrar = document.getElementById("btn-entrar");
const caixaAlerta = document.getElementById("alerta");

const REGEX_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function mostrarAlerta(mensagem, tipo) {
  caixaAlerta.textContent = mensagem;
  caixaAlerta.className = `alerta mostrar ${tipo}`;
}

function limparAlerta() {
  caixaAlerta.className = "alerta";
  caixaAlerta.textContent = "";
}

function definirErroCampo(input, idErro, mensagem) {
  document.getElementById(idErro).textContent = mensagem;
  input.classList.toggle("campo-invalido", Boolean(mensagem));
}

function validarFormulario() {
  let valido = true;

  if (!REGEX_EMAIL.test(campoEmail.value.trim())) {
    definirErroCampo(campoEmail, "erro-email", "Informe um e-mail válido.");
    valido = false;
  } else {
    definirErroCampo(campoEmail, "erro-email", "");
  }

  if (campoSenha.value.length < 1) {
    definirErroCampo(campoSenha, "erro-senha", "Informe sua senha.");
    valido = false;
  } else {
    definirErroCampo(campoSenha, "erro-senha", "");
  }

  return valido;
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  limparAlerta();

  if (!validarFormulario()) {
    return;
  }

  btnEntrar.disabled = true;
  btnEntrar.textContent = "Entrando...";

  try {
    const resposta = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: campoEmail.value.trim(),
        senha: campoSenha.value,
      }),
    });

    const dados = await resposta.json();

    if (!resposta.ok || !dados.sucesso) {
      mostrarAlerta(dados.mensagem || "Não foi possível entrar.", "erro");
      return;
    }

    mostrarAlerta(dados.mensagem, "sucesso");
    window.location.href = dados.redirect || "/dashboard";
  } catch (erro) {
    mostrarAlerta("Erro de conexão com o servidor. Tente novamente.", "erro");
  } finally {
    btnEntrar.disabled = false;
    btnEntrar.textContent = "Entrar";
  }
});

// Remove a mensagem de erro assim que o usuário volta a digitar
[campoEmail, campoSenha].forEach((campo) => {
  campo.addEventListener("input", () => campo.classList.remove("campo-invalido"));
});
