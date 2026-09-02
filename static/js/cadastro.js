// Lógica da tela de cadastro: valida os campos no navegador
// e envia os dados para o backend Flask via fetch (API REST).

const form = document.getElementById("form-cadastro");
const campoNome = document.getElementById("nome");
const campoEmail = document.getElementById("email");
const campoSenha = document.getElementById("senha");
const campoConfirmar = document.getElementById("confirmar-senha");
const btnCadastrar = document.getElementById("btn-cadastrar");
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

  if (campoNome.value.trim().length < 3) {
    definirErroCampo(campoNome, "erro-nome", "Informe seu nome completo.");
    valido = false;
  } else {
    definirErroCampo(campoNome, "erro-nome", "");
  }

  if (!REGEX_EMAIL.test(campoEmail.value.trim())) {
    definirErroCampo(campoEmail, "erro-email", "Informe um e-mail válido.");
    valido = false;
  } else {
    definirErroCampo(campoEmail, "erro-email", "");
  }

  if (campoSenha.value.length < 6) {
    definirErroCampo(campoSenha, "erro-senha", "A senha deve ter pelo menos 6 caracteres.");
    valido = false;
  } else {
    definirErroCampo(campoSenha, "erro-senha", "");
  }

  if (campoConfirmar.value !== campoSenha.value || campoConfirmar.value === "") {
    definirErroCampo(campoConfirmar, "erro-confirmar-senha", "As senhas não coincidem.");
    valido = false;
  } else {
    definirErroCampo(campoConfirmar, "erro-confirmar-senha", "");
  }

  return valido;
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  limparAlerta();

  if (!validarFormulario()) {
    return;
  }

  btnCadastrar.disabled = true;
  btnCadastrar.textContent = "Criando conta...";

  try {
    const resposta = await fetch("/api/cadastro", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome: campoNome.value.trim(),
        email: campoEmail.value.trim(),
        senha: campoSenha.value,
        confirmarSenha: campoConfirmar.value,
      }),
    });

    const dados = await resposta.json();

    if (!resposta.ok || !dados.sucesso) {
      mostrarAlerta(dados.mensagem || "Não foi possível criar a conta.", "erro");
      return;
    }

    mostrarAlerta(dados.mensagem, "sucesso");
    form.reset();
    setTimeout(() => {
      window.location.href = "/";
    }, 1200);
  } catch (erro) {
    mostrarAlerta("Erro de conexão com o servidor. Tente novamente.", "erro");
  } finally {
    btnCadastrar.disabled = false;
    btnCadastrar.textContent = "Começar agora";
  }
});

// Remove a mensagem de erro assim que o usuário volta a digitar
[campoNome, campoEmail, campoSenha, campoConfirmar].forEach((campo) => {
  campo.addEventListener("input", () => campo.classList.remove("campo-invalido"));
});
