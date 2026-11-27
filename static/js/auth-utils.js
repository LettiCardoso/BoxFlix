// Utilitários compartilhados entre as telas de login e cadastro.

const REGEX_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function mostrarAlerta(caixaAlerta, mensagem, tipo) {
  caixaAlerta.textContent = mensagem;
  caixaAlerta.className = `alerta mostrar ${tipo}`;
}

function limparAlerta(caixaAlerta) {
  caixaAlerta.className = "alerta";
  caixaAlerta.textContent = "";
}

function definirErroCampo(input, idErro, mensagem) {
  document.getElementById(idErro).textContent = mensagem;
  input.classList.toggle("campo-invalido", Boolean(mensagem));
}

function registrarLimpezaDeErro(campos) {
  campos.forEach((campo) => {
    campo.addEventListener("input", () => campo.classList.remove("campo-invalido"));
  });
}
