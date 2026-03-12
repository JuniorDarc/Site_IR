const form = document.getElementById("formulario");
const cpfInput = document.getElementById("cpf");
const loader = document.getElementById("loader");
const resultado = document.getElementById("resultado");
const btnDownload = document.getElementById("btnDownload");
const mensagem = document.getElementById("mensagem");

// máscara CPF
cpfInput.addEventListener("input", () => {
    let cpf = cpfInput.value.replace(/\D/g, "").slice(0, 11);

    cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2");
    cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2");
    cpf = cpf.replace(/(\d{3})(\d{1,2})$/, "$1-$2");

    cpfInput.value = cpf;
});

function mostrarMensagem(texto, tipo) {
    mensagem.textContent = texto;
    mensagem.className = `mensagem ${tipo}`;
    mensagem.classList.remove("hidden");
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    loader.classList.remove("hidden");
    resultado.classList.add("hidden");
    mensagem.classList.add("hidden");

    const formData = new FormData(form);

    try {
        const response = await fetch("/enviar", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const erro = await response.json();
            mostrarMensagem(erro.message, "erro");
            loader.classList.add("hidden");
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const cpfLimpo = cpfInput.value.replace(/\D/g, "");

        btnDownload.innerHTML = `📄 Baixar PDF`;

        btnDownload.onclick = () => {
            const a = document.createElement("a");
            a.href = url;
            a.download = `${cpfLimpo}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        };

        loader.classList.add("hidden");
        resultado.classList.remove("hidden");
        mostrarMensagem("Documento encontrado com sucesso.", "sucesso");

    } catch (err) {
        loader.classList.add("hidden");
        mostrarMensagem("Erro ao buscar o documento. Tente novamente.", "erro");
        console.error(err);
    }
});
