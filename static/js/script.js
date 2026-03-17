const form = document.getElementById("formulario");
const nomeInput = document.getElementById("nome");
const numeroInput = document.getElementById("numero");
const letraInput = document.getElementById("letra");
const loader = document.getElementById("loader");
const resultado = document.getElementById("resultado");
const btnDownload = document.getElementById("btnDownload");
const mensagem = document.getElementById("mensagem");

// Nome sempre em MAIÚSCULO
nomeInput.addEventListener("input", () => {
    nomeInput.value = nomeInput.value.toUpperCase();
});

// Número: apenas dígitos
numeroInput.addEventListener("input", () => {
    numeroInput.value = numeroInput.value.replace(/\D/g, "");
});

// Letra opcional: apenas uma letra e sempre em maiúsculo
letraInput.addEventListener("input", () => {
    letraInput.value = letraInput.value.toUpperCase().replace(/[^A-Z]/g, "").slice(0, 1);
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
            const erro = await response.json().catch(() => ({
                message: "Erro ao processar a solicitação."
            }));

            mostrarMensagem(erro.message || "Erro ao buscar documento.", "erro");
            loader.classList.add("hidden");
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const nome = (formData.get("nome") || "").trim();
        const numero = (formData.get("numero") || "").trim();
        const letra = (formData.get("letra") || "").trim().toUpperCase();

        const prefixo = `${numero}${letra}`;
        btnDownload.innerHTML = `📄 Baixar PDF – ${prefixo}_${nome}`;

        btnDownload.onclick = () => {
            const a = document.createElement("a");
            a.href = url;
            a.download = `${prefixo}_${nome}.pdf`;
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