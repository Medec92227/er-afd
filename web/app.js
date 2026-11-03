// Carga el paquete er_afd en Pyodide y dibuja los resultados.
const MODULOS = ["__init__.py", "parser.py", "automata.py", "cli.py", "lexer.py"];
const $ = (id) => document.getElementById(id);

let analizar = null;
let viz = null;
let datos = null;
let paso = 0;
let temporizador = null;

async function iniciar() {
  try {
    const [pyodide, instancia] = await Promise.all([loadPyodide(), Viz.instance()]);
    viz = instancia;
    pyodide.FS.mkdirTree("/home/pyodide/er_afd");
    for (const nombre of MODULOS) {
      const texto = await (await fetch(`er_afd/${nombre}`)).text();
      pyodide.FS.writeFile(`/home/pyodide/er_afd/${nombre}`, texto);
    }
    pyodide.runPython(await (await fetch("puente.py")).text());
    analizar = pyodide.globals.get("analizar");
    $("estado-carga").classList.add("oculto");
    $("convertir-btn").disabled = false;
    $("convertir-btn").textContent = "Convertir";
    leerUrl();
    convertir();
  } catch (error) {
    $("estado-carga").textContent = "No se pudo cargar Python en el navegador: " + error;
  }
}

function leerUrl() {
  const parametros = new URLSearchParams(location.search);
  if (parametros.has("er")) $("er").value = parametros.get("er");
  if (parametros.has("cadena")) $("cadena").value = parametros.get("cadena");
}

function convertir() {
  if (!analizar) return;
  detener();
  const er = $("er").value;
  const cadena = $("cadena").value;
  history.replaceState(null, "", "?" + new URLSearchParams({ er, cadena }));
  datos = JSON.parse(analizar(er, cadena));
  datos.cadena = cadena;
  $("resultado").classList.remove("oculto");
  mostrarVeredicto();
  const conAutomatas = datos.codigo !== 2;
  for (const id of ["grafo-afd", "grafo-afnd", "matriz", "subconjuntos", "consola", "cinta", "pasos"]) {
    $(id).replaceChildren();
  }
  document.querySelectorAll("#resultado article").forEach((a) => a.classList.toggle("oculto", !conAutomatas));
  if (!conAutomatas) return;
  dibujar("grafo-afd", datos.dot_afd);
  dibujar("grafo-afnd", datos.dot_afnd);
  $("resumen-afd").textContent = resumen(datos.afd, datos.afd.source_alphabet);
  $("resumen-afnd").textContent = resumen(datos.afnd, datos.afnd.alphabet);
  dibujarMatriz();
  dibujarSubconjuntos();
  $("consola").textContent = datos.consola;
  irA(datos.recorrido.length);
}

function mostrarVeredicto() {
  const caja = $("veredicto");
  caja.className = "veredicto";
  if (datos.codigo === 2) {
    caja.classList.add("error");
    caja.replaceChildren(texto("span", "Error: " + datos.error), texto("small", "código de retorno 2"));
  } else {
    caja.classList.add(datos.aceptada ? "acepta" : "rechaza");
    caja.replaceChildren(
      texto("span", datos.aceptada ? "Cadena aceptada" : "Cadena rechazada"),
      texto("small", `código de retorno ${datos.codigo} · ${datos.detenido ? "se detuvo en" : "terminó en"} ${datos.estado_final}`),
    );
  }
}

function texto(etiqueta, contenido) {
  const elemento = document.createElement(etiqueta);
  elemento.textContent = contenido;
  return elemento;
}

function resumen(automata, alfabeto) {
  return `${automata.states.length} estados · Σ={${alfabeto.join(",")}} · F={${automata.finals.join(",")}}`;
}

function dibujar(id, dot) {
  const svg = viz.renderSVGElement(dot, {
    graphAttributes: { bgcolor: "transparent", fontname: "Montserrat", fontcolor: "#eef2f6" },
    nodeAttributes: { fontname: "Montserrat", fontsize: 13, color: "#dfe7ef", fontcolor: "#eef2f6",
                      style: "filled", fillcolor: "#10263a", penwidth: 1.4 },
    edgeAttributes: { fontname: "JetBrains Mono", fontsize: 12, color: "#7f97ad", fontcolor: "#c9d6e2" },
  });
  $(id).replaceChildren(svg);
}

function dibujarMatriz() {
  const afd = datos.afd;
  const destino = {};
  for (const t of afd.transitions) destino[t.source + "|" + t.symbol] = t.target;
  const tabla = $("matriz");
  const encabezado = document.createElement("tr");
  encabezado.append(texto("th", "Estado"), ...afd.alphabet.map((s) => texto("th", s)));
  tabla.append(encabezado);
  for (const estado of afd.states) {
    const fila = document.createElement("tr");
    fila.dataset.estado = estado;
    const marca = (estado === afd.initial ? "→ " : "") + estado + (afd.finals.includes(estado) ? " *" : "");
    fila.append(texto("th", marca));
    for (const simbolo of afd.alphabet) {
      const celda = texto("td", destino[estado + "|" + simbolo] || "—");
      if (!destino[estado + "|" + simbolo]) celda.className = "vacio";
      fila.append(celda);
    }
    tabla.append(fila);
  }
  // Las clases Ci aparecen solo cuando dos conjuntos se solapan; se explican abajo.
  const clases = Object.entries(afd.partitions).filter(([nombre]) => !afd.source_alphabet.includes(nombre));
  for (const [nombre, caracteres] of clases) {
    const fila = document.createElement("tr");
    const celda = texto("td", `${nombre} = ${caracteres.length} caracteres`);
    celda.colSpan = afd.alphabet.length + 1;
    fila.append(celda);
    tabla.append(fila);
  }
}

function dibujarSubconjuntos() {
  const tabla = $("subconjuntos");
  const encabezado = document.createElement("tr");
  encabezado.append(texto("th", "AFD"), texto("th", "Estados del AFND"));
  tabla.append(encabezado);
  for (const [estado, conjunto] of Object.entries(datos.afd.subsets)) {
    const fila = document.createElement("tr");
    fila.append(texto("td", estado), texto("td", "{" + conjunto.join(",") + "}"));
    tabla.append(fila);
  }
}

function irA(nuevo) {
  const total = datos.recorrido.length;
  paso = Math.max(0, Math.min(total, nuevo));
  const actual = paso === 0 ? "Q0" : datos.recorrido[paso - 1][2];

  const cinta = $("cinta");
  cinta.replaceChildren();
  if (datos.cadena.length === 0) cinta.append(texto("span", "cadena vacía"));
  [...datos.cadena].forEach((c, i) => {
    const celda = texto("span", c === " " ? "␣" : c);
    if (i < paso) celda.className = "leido";
    if (i === paso - 1) celda.className = "actual";
    if (datos.detenido && i === total && paso === total) celda.className = "fallo";
    cinta.append(celda);
  });
  if (datos.cadena.length === 0) cinta.firstChild.className = "vacia";

  const lista = $("pasos");
  lista.replaceChildren();
  datos.recorrido.forEach((p, i) => {
    const li = texto("li", p.join("|"));
    if (i === paso - 1) li.className = "actual";
    lista.append(li);
  });
  if (paso === total) {
    let mensaje = datos.aceptada ? "Cadena aceptada" : "Cadena rechazada";
    if (datos.detenido) {
      const simbolo = datos.cadena[total] === " " ? "␣" : datos.cadena[total];
      mensaje += ` (${actual} no tiene transición con '${simbolo}')`;
    } else if (!datos.aceptada) {
      mensaje += ` (${actual} no es de aceptación)`;
    }
    const li = texto("li", mensaje);
    li.className = "final " + (datos.aceptada ? "acepta" : "rechaza");
    lista.append(li);
  }
  // Solo se desplaza la lista de pasos, no la página.
  const marcado = lista.querySelector(".actual, .final");
  if (marcado) lista.scrollTop = marcado.offsetTop - lista.offsetTop - lista.clientHeight / 2;

  resaltar(actual, paso > 0 ? datos.recorrido[paso - 1] : null);
  document.querySelectorAll("#matriz tr").forEach((f) => f.classList.toggle("activo", f.dataset.estado === actual));
}

function resaltar(estado, ultimo) {
  const svg = $("grafo-afd");
  svg.querySelectorAll(".activo").forEach((e) => e.classList.remove("activo"));
  for (const g of svg.querySelectorAll("g.node")) {
    if (g.querySelector("title")?.textContent === estado) g.classList.add("activo");
  }
  if (ultimo) {
    const arista = `${ultimo[0]}->${ultimo[2]}`;
    for (const g of svg.querySelectorAll("g.edge")) {
      if (g.querySelector("title")?.textContent === arista) g.classList.add("activo");
    }
  }
}

function reproducir() {
  if (temporizador) return detener();
  if (paso >= datos.recorrido.length) irA(0);
  $("reproducir").textContent = "⏸ Pausa";
  temporizador = setInterval(() => {
    irA(paso + 1);
    if (paso >= datos.recorrido.length) detener();
  }, 800);
}

function detener() {
  clearInterval(temporizador);
  temporizador = null;
  $("reproducir").textContent = "▶ Reproducir";
}

$("formulario").addEventListener("submit", (e) => { e.preventDefault(); convertir(); });
$("epsilon").addEventListener("click", () => {
  const campo = $("er");
  const pos = campo.selectionStart ?? campo.value.length;
  campo.setRangeText("ε", pos, campo.selectionEnd ?? pos, "end");
  campo.focus();
});
document.querySelectorAll(".tarjeta-ejemplo").forEach((b) => b.addEventListener("click", () => {
  $("er").value = b.dataset.er;
  $("cadena").value = b.dataset.cadena;
  convertir();
  $("convertir").scrollIntoView({ behavior: "smooth" });
}));
$("inicio-btn").addEventListener("click", () => { detener(); irA(0); });
$("atras").addEventListener("click", () => { detener(); irA(paso - 1); });
$("adelante").addEventListener("click", () => { detener(); irA(paso + 1); });
$("fin").addEventListener("click", () => { detener(); irA(datos.recorrido.length); });
$("reproducir").addEventListener("click", reproducir);

// Animación de aparición y pestaña activa según la sección visible.
const aparicion = new IntersectionObserver((entradas) => {
  for (const e of entradas) if (e.isIntersecting) { e.target.classList.add("visible"); aparicion.unobserve(e.target); }
}, { threshold: 0.12 });
document.querySelectorAll(".aparecer").forEach((el) => aparicion.observe(el));
const pestanas = new IntersectionObserver((entradas) => {
  for (const e of entradas) {
    if (!e.isIntersecting) continue;
    document.querySelectorAll(".pildoras a").forEach((a) => a.classList.toggle("activa", a.hash === "#" + e.target.id));
  }
}, { rootMargin: "-45% 0px -50% 0px" });
document.querySelectorAll("main > section").forEach((s) => pestanas.observe(s));

iniciar();
