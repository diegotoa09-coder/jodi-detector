/* ============================================================================
 *  JoDi · Motor de análisis  —  port fiel de detector_ia_v6.py a JavaScript
 *  100% en el navegador, sin servidor.  Mismas señales, mismos pesos.
 *  Diferencia única vs Python: sin spaCy (señal de morfología, peso 2/114).
 * ========================================================================== */
(function (global) {
"use strict";

/* ─────────────── Bancos de señales (idénticos, vía String.raw) ─────────── */
const OPENING_GPT = [
  String.raw`\ben el presente (trabajo|ensayo|documento|análisis|texto|artículo|escrito)\b`,
  String.raw`\bel (siguiente|presente) (ensayo|trabajo|documento|análisis)\b`,
  String.raw`\ba continuación (se|abordaremos|analizaremos|presentamos|exploraremos|examinaremos)\b`,
  String.raw`\bel objetivo (del presente|de este|principal|central|fundamental) (trabajo|ensayo|análisis|documento)\b`,
  String.raw`\bel propósito de (este|la presente|este trabajo|este ensayo)\b`,
  String.raw`\ba lo largo de (este|la presente|el siguiente|estas páginas)\b`,
  String.raw`\ben las siguientes (líneas|páginas|secciones|páginas)\b`,
  String.raw`\bprocederemos a (analizar|explorar|examinar|estudiar|abordar)\b`,
  String.raw`\bnos (proponemos|disponemos) a (analizar|explorar|examinar)\b`,
  String.raw`\bel presente (análisis|trabajo|documento|ensayo|escrito) (tiene|busca|pretende|tiene como objetivo)\b`,
  String.raw`\besta (investigación|reflexión|exposición) (tiene|busca|pretende|tiene como objetivo)\b`,
  String.raw`\bin this (essay|paper|work|analysis|study|piece)\b`,
  String.raw`\bthis (essay|paper|work|analysis|study) (will|aims to|seeks to|explores|examines|discusses)\b`,
  String.raw`\bthe following (essay|paper|analysis|study|work)\b`,
  String.raw`\bin the following (sections|pages|lines|paragraphs)\b`,
  String.raw`\bthis (paper|study|analysis) (will|aims to) (explore|examine|analyze|discuss|investigate)\b`,
  String.raw`\bthe purpose of this\b`,
  String.raw`\bthe aim of this\b`,
  String.raw`\bthe objective of this\b`,
];

const CLOSING_GPT = [
  String.raw`\ben conclusión[,\s]`,
  String.raw`\ben resumen[,\s]`,
  String.raw`\ben definitiva[,\s]`,
  String.raw`\ba modo de conclusión\b`,
  String.raw`\bpara concluir[,\s]`,
  String.raw`\bpara finalizar[,\s]`,
  String.raw`\bcomo (hemos visto|se ha visto|se puede observar|hemos podido ver|hemos analizado)\b`,
  String.raw`\bde todo lo anterior (se puede|podemos|cabe|se desprende)\b`,
  String.raw`\ba partir de lo expuesto\b`,
  String.raw`\bpor todo lo (anterior|expuesto|mencionado|analizado)\b`,
  String.raw`\blos aspectos (analizados|expuestos|mencionados|desarrollados) (permiten|nos permiten|muestran)\b`,
  String.raw`\blo expuesto (anteriormente|hasta aquí|en este|a lo largo)\b`,
  String.raw`\bqueda (claro|demostrado|evidenciado|patente) que\b`,
  String.raw`\bpodemos (concluir|afirmar|sostener|señalar) que\b`,
  String.raw`\bin conclusion[,\s]`,
  String.raw`\bto (conclude|summarize|sum up)[,\s]`,
  String.raw`\bin summary[,\s]`,
  String.raw`\bto sum (up|things up)[,\s]`,
  String.raw`\bas (we have|we've) (seen|discussed|explored|examined|analyzed)\b`,
  String.raw`\boverall[,\s]`,
  String.raw`\ball in all[,\s]`,
  String.raw`\btaking everything into account\b`,
  String.raw`\bbringing (it|everything|this) together\b`,
];

const TRANSITION_GPT = [
  String.raw`\ben primer lugar\b`, String.raw`\ben segundo lugar\b`, String.raw`\ben tercer lugar\b`,
  String.raw`\ben cuarto lugar\b`, String.raw`\bfinalmente[,\s]`,
  String.raw`\bpor otro lado\b`, String.raw`\bpor una parte\b`, String.raw`\bpor otra parte\b`,
  String.raw`\ben este sentido\b`, String.raw`\ben el ámbito de\b`,
  String.raw`\bdesde esta perspectiva\b`, String.raw`\ben el marco de\b`,
  String.raw`\ba partir de lo anterior\b`, String.raw`\ben virtud de lo expuesto\b`,
  String.raw`\bde acuerdo con lo anterior\b`, String.raw`\ben tal sentido\b`,
  String.raw`\bpor lo expuesto\b`, String.raw`\blo anteriormente mencionado\b`,
  String.raw`\bcomo se mencionó (anteriormente|antes|previamente)\b`,
  String.raw`\btal como se indicó\b`, String.raw`\btal y como (se|hemos)\b`,
  String.raw`\bes por ello que\b`, String.raw`\bes por esto que\b`, String.raw`\bes por eso que\b`,
  String.raw`\ben este (contexto|escenario|marco|orden de ideas)\b`,
  String.raw`\bante (este|esta|estos|estas) (panorama|situación|contexto|realidad|escenario)\b`,
  String.raw`\bdesde este (punto de vista|enfoque|ángulo|perspectiva)\b`,
  String.raw`\btomando en cuenta (lo anterior|lo expuesto|esto)\b`,
  String.raw`\ba raíz de (lo anterior|esto|ello|lo expuesto)\b`,
  String.raw`(^|\.\s+)asimismo[,\s]`, String.raw`(^|\.\s+)igualmente[,\s]`,
  String.raw`(^|\.\s+)de igual (manera|forma|modo)[,\s]`,
  String.raw`(^|\.\s+)por su parte[,\s]`, String.raw`(^|\.\s+)por consiguiente[,\s]`,
  String.raw`(^|\.\s+)en consecuencia[,\s]`, String.raw`(^|\.\s+)dicho esto[,\s]`,
  String.raw`\ben última instancia\b`, String.raw`\ben este orden de ideas\b`,
  String.raw`\bcada vez más (popular|relevante|importante|frecuente|común|presente)\b`,
  String.raw`\bfurthermore[,\s]`, String.raw`\bmoreover[,\s]`, String.raw`\badditionally[,\s]`,
  String.raw`\bin addition[,\s]`, String.raw`\bnevertheless[,\s]`, String.raw`\bnonetheless[,\s]`,
  String.raw`\bin light of\b`, String.raw`\bwith regard to\b`, String.raw`\bwith respect to\b`,
  String.raw`\bon the other hand\b`, String.raw`\bon one hand\b`,
  String.raw`\bby the same token\b`, String.raw`\bin this regard\b`, String.raw`\bin this context\b`,
  String.raw`\bbuilding on (this|that|these)\b`,
  String.raw`\bwith this in mind\b`, String.raw`\bbearing this in mind\b`,
];

const EMPHASIS_GPT = [
  String.raw`\bes importante (destacar|señalar|mencionar|tener en cuenta|recalcar|subrayar|notar)\b`,
  String.raw`\bcabe (mencionar|señalar|destacar|preguntarse|reflexionar|aclarar|precisar)\b`,
  String.raw`\bresulta (fundamental|esencial|crucial|importante|relevante|necesario|pertinente)\b`,
  String.raw`\bes (preciso|necesario|indispensable|imprescindible|menester) (señalar|mencionar|destacar|considerar|tener|recordar)\b`,
  String.raw`\bconviene (destacar|mencionar|señalar|recordar|aclarar|precisar)\b`,
  String.raw`\bvale la pena (mencionar|destacar|señalar|recordar|considerar|aclarar)\b`,
  String.raw`\bno cabe duda\b`, String.raw`\bsin lugar a dudas\b`, String.raw`\bno hay duda de que\b`,
  String.raw`\bes (indudable|innegable|evidente|claro|obvio|patente|manifiesto) que\b`,
  String.raw`\bhay que tener en cuenta\b`, String.raw`\bes importante tener en cuenta\b`,
  String.raw`\bes necesario tener en cuenta\b`,
  String.raw`\bse puede (observar|concluir|afirmar|notar|apreciar|ver)\b`,
  String.raw`\bpodemos (observar|destacar|concluir|afirmar|señalar|notar|ver|apreciar)\b`,
  String.raw`\bse hace (necesario|evidente|imprescindible|patente|urgente)\b`,
  String.raw`\bes (por tanto|por ello|por ende) (fundamental|necesario|importante|crucial)\b`,
  String.raw`\bjuega(n)? un papel (fundamental|crucial|importante|clave|determinante|esencial|central|preponderante)\b`,
  String.raw`\bdesempeña(n)? un papel (fundamental|crucial|importante|clave|central)\b`,
  String.raw`\btiene(n)? un (papel|rol|impacto|efecto) (fundamental|crucial|importante|clave|significativo)\b`,
  String.raw`\bes de (suma|vital|capital) importancia\b`,
  String.raw`\bno se puede (ignorar|negar|desconocer|pasar por alto)\b`,
  String.raw`\bsería (un error|incorrecto|inadecuado) (ignorar|negar|desconocer)\b`,
  String.raw`\bit is (worth noting|important to|crucial|essential|vital|necessary to|imperative to)\b`,
  String.raw`\bit (should|must) be (noted|mentioned|highlighted|emphasized|stressed|acknowledged)\b`,
  String.raw`\bit is (clear|evident|obvious|undeniable|worth emphasizing) that\b`,
  String.raw`\bone (must|should|can|cannot) (consider|ignore|overlook|deny|underestimate)\b`,
  String.raw`\bplays a (crucial|key|vital|important|central|fundamental|pivotal|significant) role\b`,
  String.raw`\bit goes without saying\b`, String.raw`\bneedless to say\b`,
  String.raw`\bit is (no coincidence|no surprise|not surprising) that\b`,
  String.raw`\bit would be (remiss|wrong|incorrect) to (ignore|overlook|neglect)\b`,
  String.raw`\bwe (cannot|can't|must not) (ignore|overlook|underestimate)\b`,
  String.raw`\bof (particular|special|great|utmost|paramount) importance\b`,
  String.raw`\bit bears (mentioning|repeating|emphasizing)\b`,
];

const GENERIC_GPT = [
  String.raw`\bhoy (en día|día)\b`,
  String.raw`\ben la actualidad\b`,
  String.raw`\ben el mundo actual\b`,
  String.raw`\bdesde (tiempos inmemoriales|siempre|antaño)\b`,
  String.raw`\ba nivel (global|mundial|nacional|social|local|internacional)\b`,
  String.raw`\bel ser humano\b`, String.raw`\blos seres humanos\b`,
  String.raw`\bla sociedad (actual|moderna|contemporánea|de hoy|globalizada)\b`,
  String.raw`\bel mundo (actual|moderno|contemporáneo|globalizado|de hoy|digital)\b`,
  String.raw`\blo largo de la historia\b`,
  String.raw`\ba través del tiempo\b`, String.raw`\ba lo largo del tiempo\b`,
  String.raw`\ben todos los ámbitos\b`, String.raw`\ben diversos ámbitos\b`,
  String.raw`\bun papel (fundamental|crucial|importante|clave) en la sociedad\b`,
  String.raw`\bnuevo paradigma\b`, String.raw`\bnuevos paradigmas\b`, String.raw`\bcambio de paradigma\b`,
  String.raw`\bun sinfín de\b`,
  String.raw`\bun amplio (abanico|espectro|rango|conjunto) de\b`,
  String.raw`\bpermite(n)? (comprender|analizar|observar|identificar|abordar|entender)\b`,
  String.raw`\bgenera(n)? un (impacto|cambio|beneficio|efecto) (positivo|negativo|significativo)?\b`,
  String.raw`\bthroughout history\b`,
  String.raw`\bin today's (world|society|era|age|digital age|fast-paced world)\b`,
  String.raw`\bin the modern (world|era|age|society|landscape)\b`,
  String.raw`\bhas become (increasingly|ever more|more and more)\b`,
  String.raw`\bin recent (years|decades|times|history)\b`,
  String.raw`\bwith the (advent|rise|emergence|dawn|proliferation) of\b`,
  String.raw`\bthe importance of (this|these|such)\b`,
  String.raw`\bdelve into\b`, String.raw`\bunpack (this|the|these)\b`,
  String.raw`\bnavigate (the|this|these|complex|ever-changing)\b`,
  String.raw`\bthe (rapidly|ever|constantly) (changing|evolving|shifting) (world|landscape|environment)\b`,
  String.raw`\bin an (increasingly|ever more) (connected|globalized|digital|complex) world\b`,
  String.raw`\bmore than ever (before)?\b`,
  String.raw`\bthe (digital|information|technological) (age|era|revolution)\b`,
  String.raw`\bstand the test of time\b`,
  String.raw`\bseparate the wheat from the chaff\b`,
  String.raw`\bat the forefront of\b`,
  String.raw`\ba (double-edged|two-edged) sword\b`,
  String.raw`\bthe elephant in the room\b`,
  String.raw`\ba (game[- ]changer|paradigm shift)\b`,
];

const GPT_VOCAB = [
  "fundamental","esencial","crucial","vital","primordial","indispensable","imprescindible",
  "relevante","significativo","considerable","innegable","indudable","evidente","notable",
  "sustancial","determinante","trascendental","preponderante","paradigma","sinergia",
  "complejidad","perspectiva","panorama","ámbito","entorno","contexto","marco","tejido",
  "ecosistema","dinámica","dimensión","eje","pilar","vector","desafío","abordar","abordará",
  "abordaremos","ahondar","profundizar","implementar","implementación","optimizar","potenciar",
  "enfatizar","destacar","resaltar","subrayar","visibilizar","promover","fomentar","impulsar",
  "fortalecer","evidentemente","claramente","ciertamente","innegablemente","indudablemente",
  "inevitablemente","necesariamente","holístico","integral","transversal","multidimensional",
  "multifacético","articulado","cohesionado","robusto","diverso","variado","numeroso","múltiple",
  "substantial","significant","notable","remarkable","profound","comprehensive","extensive",
  "nuanced","intricate","complex","pivotal","paramount","imperative","leverage","synergy",
  "underscore","emphasize","highlight","facilitate","streamline","utilize","implement","optimize",
  "navigate","foster","multifaceted","robust","transformative","innovative","dynamic","ecosystem",
  "landscape","framework","paradigm","dimension","delve","unpack","unravel","elucidate",
  "illuminate","crucial","vital","essential","fundamental","cornerstone","holistic",
  "comprehensive","integral","overarching",
];

const EVAL_ADJECTIVES = [
  "fundamental","esencial","crucial","vital","importante","significativo","relevante","notable",
  "considerable","determinante","trascendental","innegable","indudable","evidente","claro","obvio",
  "necesario","indispensable","imprescindible","sustancial","primordial","preponderante",
  "important","significant","crucial","essential","vital","notable","substantial","considerable",
  "evident","clear","necessary","fundamental","critical","key","central",
];

const HUMAN_MARKERS = [
  String.raw`\.{3}`,
  String.raw`[!¡]{1,3}`,
  String.raw`[?¿]{2,}`,
  String.raw`\b(bueno|pues|o sea|o sea que|la verdad|en fin|igual|type)\b`,
  String.raw`\b(creo que|me parece|no sé|no estoy seguro|supongo)\b`,
  String.raw`\b(jaja|je|haha|lol|xd)\b`,
  String.raw`—`,
  String.raw`\b(también|aunque sea|al menos|por lo menos|más o menos)\b`,
  String.raw`\b(eso sí|eso no|claro que|desde luego|por supuesto)\b`,
  String.raw`\b(anyway|tbh|tbf|ngl|imo|imho|afaik)\b`,
  String.raw`[,]{2,}`,
];

const BALANCED_SYNTAX = [
  String.raw`\b(por un lado).{5,80}(por otro lado)\b`,
  String.raw`\b(tanto).{3,50}(como)\b.{3,40}(son|representan|constituyen|permiten)\b`,
  String.raw`\bnot only.{5,80}but also\b`,
  String.raw`\bon the one hand.{5,100}on the other hand\b`,
  String.raw`\bno solo.{5,80}sino (también|además)\b`,
  String.raw`\bsi bien.{5,80}(también|igualmente|asimismo)\b`,
  String.raw`\b(aunque|a pesar de que).{5,60}(sin embargo|no obstante|pero)\b`,
  String.raw`\b(a medida que|conforme).{5,60}(también|igualmente|a su vez)\b`,
  String.raw`\b(X|Y)\b.{2,20}(juega un papel|desempeña un papel|tiene un papel).{5,40}(también|igualmente|asimismo)\b`,
];

const IMPLICIT_LIST_SRC =
  String.raw`(también es|también (resulta|representa|constituye|puede)|igualmente (es|resulta|representa)|de igual (manera|forma|modo)[, ].{5,60}(es|resulta|representa|constituye)|asimismo[, ].{5,60}(es|resulta|permite|contribuye))`;

const PASSIVE_SRC =
  String.raw`\b(fue|fueron|es|son|era|eran|ha sido|han sido|se puede|se debe|se considera|se observa|se evidencia|se destaca|se menciona|se establece|se determina|se presenta|se utiliza|se emplea|se aplica|se realiza|se lleva a cabo|se ha (demostrado|señalado|indicado|establecido)|was|were|is being|are being|has been|have been|it was (found|noted|observed|established|shown|demonstrated))\b`;

const CONNECTOR_SRC =
  String.raw`\b(sin embargo|aunque|no obstante|por lo tanto|debido a|a pesar de|con respecto a|en cuanto a|asimismo|igualmente|de igual manera|por consiguiente|en consecuencia|dado que|puesto que|ya que|debido a que|por ende|así pues|en efecto|ciertamente|efectivamente|however|although|therefore|consequently|nevertheless|furthermore|additionally|moreover|in addition)\b`;

const PARA_STARTER_SRC =
  String.raw`^(Además|Por otro lado|Por otra parte|Sin embargo|No obstante|En conclusión|En resumen|En definitiva|Por lo tanto|Por consiguiente|Asimismo|De igual manera|De este modo|De esta manera|Cabe destacar|Es importante|Resulta fundamental|En este sentido|En este contexto|A su vez|Del mismo modo|De igual forma|Por su parte|Furthermore|Moreover|Additionally|However|In conclusion|In summary|Therefore|Nevertheless|Consequently|It is important|It should be noted|It is worth|Building on|With this in mind),?\s`;

const ACTION_VERBS_SRC =
  String.raw`\b(fui|fue|hice|hizo|llegué|llegó|compré|compró|dije|dijo|vi|vio|salí|salió|entré|entró|encontré|encontró|went|came|said|told|saw|bought|found|got|took|made|called|walked|ran|looked|tried|thought|felt)\b`;

const FALLBACK_STOPWORDS = new Set([
  "de","la","el","en","y","a","los","del","se","las","por","un","para","con","no","una","su","al",
  "es","lo","como","más","pero","sus","le","ya","o","fue","este","ha","si","the","of","and","in",
  "is","it","to","that","was","for","on","are","with","as","at","be","by","from","this","were",
  "they","them","their","there","been","have","has","had","would","could","should","will","what",
  "when","where","who","which","than","then","also","about","into","over",
]);

/* Stopwords NLTK (es+en) — volcadas de la instalación real (504) */
const STOPWORDS = new Set(STOPWORDS_LIST());

/* ─────────────── Compilación de regex ─────────────── */
function compile(list, flags){ return list.map(p => new RegExp(p, flags)); }
function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function reWord(w){ return new RegExp("(?<![\\p{L}\\p{N}_])"+esc(w)+"(?![\\p{L}\\p{N}_])", "iu"); }

const RE_OPENING    = compile(OPENING_GPT, "i");
const RE_CLOSING    = compile(CLOSING_GPT, "i");
const RE_TRANSITION = compile(TRANSITION_GPT, "i");
const RE_EMPHASIS   = compile(EMPHASIS_GPT, "i");
const RE_GENERIC    = compile(GENERIC_GPT, "i");
const RE_HUMAN      = compile(HUMAN_MARKERS, "i");
const RE_BALANCED   = compile(BALANCED_SYNTAX, "is");
const RE_VOCAB      = GPT_VOCAB.map(reWord);
const RE_EVALADJ    = EVAL_ADJECTIVES.map(reWord);
const RE_IMPLICIT   = new RegExp(IMPLICIT_LIST_SRC, "gi");
const RE_PASSIVE    = new RegExp(PASSIVE_SRC, "gi");
const RE_CONNECTOR  = new RegExp(CONNECTOR_SRC, "gi");
const RE_PARASTART  = new RegExp(PARA_STARTER_SRC, "i");
const RE_ACTION     = new RegExp(ACTION_VERBS_SRC, "gi");

/* ─────────────── Helpers ─────────────── */
const clamp = (x, lo, hi) => Math.max(lo, Math.min(x, hi));
function countSearch(reList, text){ let n=0; for(const re of reList) if(re.test(text)) n++; return n; }
function countAll(re, text){ const m = text.match(re); return m ? m.length : 0; }

function tokenizeSentences(text){
  return text.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 10);
}
function tokenizeWords(text){
  return (text.toLowerCase().match(/\p{L}{2,}/gu)) || [];
}

/* ─────────────── Métricas ─────────────── */
function countSyllablesEs(word){
  const vowels = "aeiouáéíóúü";
  let count = 0, prevV = false;
  for(const ch of word.toLowerCase()){
    const isV = vowels.includes(ch);
    if(isV && !prevV) count++;
    prevV = isV;
  }
  return Math.max(count, 1);
}
function readabilityFH(words, sentences){
  if(!words.length || !sentences.length) return 50.0;
  let sylls = 0; for(const w of words) sylls += countSyllablesEs(w);
  const nW = Math.max(words.length,1), nS = Math.max(sentences.length,1);
  const score = 206.835 - 0.60*(sylls/nW)*100 - 1.02*(nW/nS);
  return clamp(score, 0.0, 100.0);
}
function sentenceUniformity(sentences){
  const lengths = sentences.map(s => s.split(/\s+/).filter(Boolean).length).filter(l => l>1);
  if(lengths.length < 2) return [0.5, lengths.length ? lengths[0] : 0];
  const avg = lengths.reduce((a,b)=>a+b,0)/lengths.length;
  const std = Math.sqrt(lengths.reduce((a,l)=>a+(l-avg)**2,0)/lengths.length);
  const cv = std/Math.max(avg,1);
  const signal = Math.max(0.0, 1.0 - Math.min(cv/0.35, 1.0));
  return [signal, avg];
}
function burstiness(sentences){
  const lengths = sentences.map(s => s.split(/\s+/).filter(Boolean).length).filter(l => l>1);
  if(lengths.length < 5) return 0.5;
  const mean = lengths.reduce((a,b)=>a+b,0)/lengths.length;
  const std = Math.sqrt(lengths.reduce((a,l)=>a+(l-mean)**2,0)/lengths.length);
  const b = (std-mean)/(std+mean+1e-9);
  return clamp((-b+1.0)/2.0, 0.0, 1.0);
}
function lexicalEntropy(words){
  if(!words.length) return 0.0;
  const counts = new Map();
  for(const w of words) counts.set(w, (counts.get(w)||0)+1);
  const total = words.length;
  let ent = 0; for(const c of counts.values()){ const p=c/total; ent -= p*Math.log2(p); }
  const maxE = total>1 ? Math.log2(total) : 1.0;
  return ent/maxE;
}
function repetitiveNgrams(words, n){
  if(words.length < n) return 0.0;
  const counts = new Map();
  const total = words.length - n + 1;
  for(let i=0;i<total;i++){
    const g = words.slice(i,i+n).join("");
    counts.set(g, (counts.get(g)||0)+1);
  }
  let repeated = 0; for(const c of counts.values()) if(c>1) repeated++;
  return Math.min(repeated/Math.max(total,1)*12, 1.0);
}
function paragraphAnalysis(text){
  const paragraphs = text.split("\n").map(p=>p.trim()).filter(p=>p.length>20);
  if(!paragraphs.length) return [0.0,0.0,0.0];
  let gptStarts = 0;
  for(const p of paragraphs) if(RE_PARASTART.test(p)) gptStarts++;
  const startRatio = gptStarts/paragraphs.length;
  let paraUniform = 0.0;
  if(paragraphs.length > 1){
    const lens = paragraphs.map(p=>p.split(/\s+/).filter(Boolean).length);
    const avg = lens.reduce((a,b)=>a+b,0)/lens.length;
    const std = Math.sqrt(lens.reduce((a,l)=>a+(l-avg)**2,0)/lens.length);
    paraUniform = Math.max(0.0, 1.0 - Math.min(std/Math.max(avg,1), 1.0));
  }
  const implicitHits = countAll(RE_IMPLICIT, text);
  const implicitSignal = Math.min(implicitHits/Math.max(paragraphs.length,1)*2, 1.0);
  return [startRatio, paraUniform, implicitSignal];
}
function balancedSyntaxScore(text){
  let hits=0; for(const re of RE_BALANCED) if(re.test(text)) hits++;
  return Math.min(hits/3.0, 1.0);
}
function evalAdjectiveRatio(textLower){
  let evalHits=0; for(const re of RE_EVALADJ) if(re.test(textLower)) evalHits++;
  const actions = countAll(RE_ACTION, textLower);
  const ratio = evalHits/Math.max(actions+1, 1);
  return Math.min(ratio/4.0, 1.0);
}
function humanMarkersScore(text){
  let hits=0; for(const re of RE_HUMAN) if(re.test(text)) hits++;
  return Math.min(hits/4.0, 1.0);
}
function informalPunctuationScore(text){
  const cnt = (s)=> text.split(s).length-1;
  const informal = cnt("...")*2 + cnt("!") + cnt("¡") + cnt("—") +
    countAll(/\?{2,}/g, text) + countAll(/!{2,}/g, text)*2;
  const density = informal/Math.max(text.length/100, 1);
  return Math.min(density/3.0, 1.0);
}
function semanticRedundancy(sentences){
  if(sentences.length < 3) return 0.0;
  const overlaps = [];
  for(let i=0;i<sentences.length-1;i++){
    const w1 = (sentences[i].toLowerCase().match(/[a-záéíóúñ]{4,}/gu)||[]);
    const w2 = (sentences[i+1].toLowerCase().match(/[a-záéíóúñ]{4,}/gu)||[]);
    const s1 = new Set(w1.filter(w=>!FALLBACK_STOPWORDS.has(w)));
    const s2 = new Set(w2.filter(w=>!FALLBACK_STOPWORDS.has(w)));
    if(s1.size && s2.size){
      let inter=0; for(const w of s1) if(s2.has(w)) inter++;
      const uni = new Set([...s1,...s2]).size;
      overlaps.push(inter/uni);
    }
  }
  if(!overlaps.length) return 0.0;
  const avg = overlaps.reduce((a,b)=>a+b,0)/overlaps.length;
  if(avg >= 0.12 && avg <= 0.45) return Math.min(avg*3, 1.0);
  return 0.0;
}
function zoneAnalysis(sentences){
  const n = sentences.length;
  if(n < 4) return {intro:0.0, body:0.0, closing:0.0};
  const introEnd = Math.max(1, Math.floor(n/4));
  const closingStart = Math.max(introEnd+1, n - Math.floor(n/4));
  const introText = sentences.slice(0,introEnd).join(" ").toLowerCase();
  const closingText = sentences.slice(closingStart).join(" ").toLowerCase();
  const bodySents = sentences.slice(introEnd, closingStart);
  const bodyText = bodySents.join(" ").toLowerCase();
  const introHits = countSearch(RE_OPENING, introText);
  const closingHits = countSearch(RE_CLOSING, closingText);
  const bodyHits = countSearch(RE_EMPHASIS, bodyText);
  return {
    intro:   Math.min(introHits/2.0, 1.0),
    body:    Math.min(bodyHits/Math.max(bodySents.length,1)*2, 1.0),
    closing: Math.min(closingHits/2.0, 1.0),
  };
}
function pct(hits, threshold){ return Math.round(Math.min(hits/threshold, 1.0)*100); }

/* ─────────────── Motor principal ─────────────── */
function analyzeText(text){
  text = text || "";
  const sentences = tokenizeSentences(text);
  const allWords  = tokenizeWords(text);
  const textLower = text.toLowerCase();

  const contentWords = allWords.filter(w => !STOPWORDS.has(w) && w.length>2);
  const wordCount = Math.max(allWords.length, 1);
  const sentCount = Math.max(sentences.length, 1);

  const openingHits    = countSearch(RE_OPENING, textLower);
  const closingHits    = countSearch(RE_CLOSING, textLower);
  const transitionHits = countSearch(RE_TRANSITION, textLower);
  const emphasisHits   = countSearch(RE_EMPHASIS, textLower);
  const genericHits    = countSearch(RE_GENERIC, textLower);
  const totalHits = openingHits+closingHits+transitionHits+emphasisHits+genericHits;

  const phraseThreshold = Math.max(2.5, wordCount/65);
  const phraseDensity = Math.min(totalHits/phraseThreshold, 1.0);

  const categoriesFiring = [openingHits,closingHits,transitionHits,emphasisHits,genericHits]
    .filter(h=>h>0).length;
  const cooccurSignal = Math.min(Math.max(categoriesFiring-1,0)/3.0, 1.0);

  let gptVocabHits = 0; for(const re of RE_VOCAB) if(re.test(textLower)) gptVocabHits++;
  const vocabThreshold = Math.max(4.0, wordCount/75);
  const vocabSignal = Math.min(gptVocabHits/vocabThreshold, 1.0);

  const [uniformity, avgSentLen] = sentenceUniformity(sentences);

  const [paraStart, paraUniform, implicitList] = paragraphAnalysis(text);
  const paraSignal = paraStart*0.55 + paraUniform*0.30 + implicitList*0.15;

  const burstSignal = burstiness(sentences);

  const connectorCount = countAll(RE_CONNECTOR, text);
  const connectorDensity = Math.min(connectorCount/sentCount/0.40, 1.0);

  const ngramSignal = repetitiveNgrams(contentWords, 3);

  const passiveCount = countAll(RE_PASSIVE, text);
  const passiveRatio = Math.min(passiveCount/sentCount/0.75, 1.0);

  const redundancySignal = semanticRedundancy(sentences);
  const syntaxSignal = balancedSyntaxScore(text);
  const evalAdjSignal = evalAdjectiveRatio(textLower);

  const entropy = lexicalEntropy(contentWords);
  let entropySignal;
  if(entropy >= 0.68 && entropy <= 0.93) entropySignal = 0.65;
  else if(entropy > 0.93) entropySignal = 0.35;
  else entropySignal = 0.30;

  const zones = zoneAnalysis(sentences);
  const zoneSignal = zones.intro*0.40 + zones.body*0.30 + zones.closing*0.30;

  // spaCy no disponible en navegador → señal de morfología 0
  const posSignal = 0.0;
  const SPACY_OK = false, NLTK_OK = false;

  const fk = readabilityFH(allWords, sentences);
  const fkSignal = (fk>=48 && fk<=80) ? 0.60 : (fk>80 ? 0.40 : 0.20);

  const ttr = (new Set(contentWords)).size / Math.max(contentWords.length, 1);
  const ttrSignal = (ttr>=0.36 && ttr<=0.70) ? 0.55 : (ttr<0.36 ? 0.30 : 0.35);

  const humanSignal = humanMarkersScore(text);
  const informalPunct = informalPunctuationScore(text);
  const humanPenalty = humanSignal*0.60 + informalPunct*0.40;

  const weights = {
    phrase_density:27, cooccur_signal:11, vocab_signal:12, uniformity:9, para_signal:8,
    zone_signal:7, connector_density:6, burst_signal:5, eval_adj_signal:4, redundancy_signal:4,
    syntax_signal:4, ngram_signal:3, entropy_signal:3, passive_ratio:2, pos_signal:2,
    fk_signal:1, ttr_signal:0,
  };
  const values = {
    phrase_density:phraseDensity, cooccur_signal:cooccurSignal, vocab_signal:vocabSignal,
    uniformity:uniformity, para_signal:paraSignal, zone_signal:zoneSignal,
    connector_density:connectorDensity, burst_signal:burstSignal, eval_adj_signal:evalAdjSignal,
    redundancy_signal:redundancySignal, syntax_signal:syntaxSignal, ngram_signal:ngramSignal,
    entropy_signal:entropySignal, passive_ratio:passiveRatio, pos_signal:posSignal,
    fk_signal:fkSignal, ttr_signal:ttrSignal,
  };
  let totalW = 0; for(const k in weights) totalW += weights[k];
  let raw = 0; for(const k in weights) raw += values[k]*weights[k];
  let rawScore = raw/totalW*100;

  const gptEvidence = Math.min(
    (totalHits/6.0)*0.40 + cooccurSignal*0.35 + vocabSignal*0.25, 1.0);
  const penaltyFactor = (1.0-gptEvidence)*0.26;
  rawScore = rawScore*(1.0 - humanPenalty*penaltyFactor);

  if(totalHits>=8 && categoriesFiring>=3) rawScore = rawScore + (100-rawScore)*0.18;

  const lengthFactor = Math.min(contentWords.length/60, 1.0);
  const phraseBoost = Math.min(totalHits/4.0, 1.0)*0.30;
  const evidenceBoost = gptEvidence*0.20;
  const effLength = Math.min(lengthFactor+phraseBoost+evidenceBoost, 1.0);
  let aiScore = rawScore*effLength + 50.0*(1.0-effLength);
  aiScore = clamp(aiScore, 2, 97);

  let confidence = 48.0;
  confidence += Math.min(contentWords.length/5.5, 32);
  if(SPACY_OK) confidence += 6;
  if(NLTK_OK)  confidence += 5;
  if(sentences.length>=5) confidence += 3;
  if(totalHits>=3) confidence += 5;
  if(totalHits>=8) confidence += 3;
  confidence = Math.min(confidence, 95);

  const signals = [
    ["Frases de apertura/cierre GPT", pct(Math.max(openingHits,closingHits),3)],
    ["Frases de énfasis IA", pct(emphasisHits,5)],
    ["Conectores/transiciones GPT", pct(transitionHits,6)],
    ["Frases genéricas/cliché", pct(genericHits,6)],
    ["Vocabulario GPT sobreusado", Math.round(vocabSignal*100)],
    ["Uniformidad de oraciones", Math.round(uniformity*100)],
    ["Estructura de párrafos", Math.round(paraSignal*100)],
    ["Patrón por zonas (intro/cierre)", Math.round(zoneSignal*100)],
    ["Burstiness (variación ritmo)", Math.round(burstSignal*100)],
    ["Adjetivos evaluativos", Math.round(evalAdjSignal*100)],
    ["Redundancia semántica", Math.round(redundancySignal*100)],
    ["Sintaxis balanceada/formulaica", Math.round(syntaxSignal*100)],
    ["N-gramas repetidos", Math.round(ngramSignal*100)],
    ["Entropía léxica", Math.round(entropySignal*100)],
    ["Voz pasiva / impersonal", Math.round(passiveRatio*100)],
    ["Rasgos humanos detectados ↓", Math.round(humanPenalty*100)],
  ];

  return {
    ai_score: Math.round(aiScore),
    confidence: Math.round(confidence),
    word_count: allWords.length,
    sentence_count: sentCount,
    avg_words_per_sentence: Math.round(avgSentLen*10)/10,
    lexical_diversity: Math.round(ttr*1000)/10,
    lexical_entropy: Math.round(entropy*1000)/10,
    ai_phrases_total: totalHits,
    phrase_categories: {
      apertura: openingHits, cierre: closingHits, "transición": transitionHits,
      "énfasis": emphasisHits, "clichés": genericHits,
    },
    gpt_vocab_found: gptVocabHits,
    readability: Math.round(fk*10)/10,
    human_signal: Math.round(humanPenalty*100),
    zones: zones,
    spacy_active: SPACY_OK,
    nltk_active: NLTK_OK,
    signals: signals,
  };
}

/* ─────────────── Informe HTML imprimible ─────────────── */
function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, c =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function verdictFor(s){
  if(s>=70) return ["PROBABLE ORIGEN ARTIFICIAL", "#f87171"];
  if(s>=45) return ["RESULTADO MIXTO / INCIERTO", "#fbbf24"];
  return ["PROBABLE ORIGEN HUMANO", "#34d399"];
}
function buildHtmlReport(r){
  const score = r.ai_score;
  const [verdict, vcol] = verdictFor(score);
  const ts = new Date().toLocaleString("es");
  const sigColor = (v, human)=> human ? "#34d399" : (v>65?"#f87171":(v>35?"#fbbf24":"#34d399"));
  const barRows = (items, human=false) => items.map(([name,val])=>{
    const clean = escapeHtml(name.replace(" ↓",""));
    const col = sigColor(val, human);
    return `<tr><td class="sig">${clean}</td>
      <td class="track"><span style="width:${val}%;background:${col}"></span></td>
      <td class="pct">${val}%</td></tr>`;
  }).join("");
  const ia = r.signals.filter(s=>!s[0].includes("↓"));
  const hu = r.signals.filter(s=>s[0].includes("↓"));
  const metrics = [
    ["Palabras", r.word_count], ["Oraciones", r.sentence_count],
    ["Prom. palabras/oración", r.avg_words_per_sentence],
    ["Diversidad léxica (TTR)", r.lexical_diversity+"%"],
    ["Entropía léxica", r.lexical_entropy+"%"],
    ["Frases IA detectadas", r.ai_phrases_total],
    ["Vocabulario GPT", r.gpt_vocab_found],
    ["Legibilidad (F-Huerta)", r.readability],
    ["Señal de humanidad", r.human_signal+"%"],
    ["Confianza del análisis", r.confidence+"%"],
  ];
  const metricCells = metrics.map(([l,v])=>
    `<div class="m"><span class="ml">${escapeHtml(l)}</span><span class="mv">${escapeHtml(v)}</span></div>`).join("");
  const catCells = Object.entries(r.phrase_categories).map(([k,v])=>
    `<div class="c"><span class="cl">${escapeHtml(k.toUpperCase())}</span><span class="cv">${v}</span></div>`).join("");

  return `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Informe JoDi — Análisis de texto</title><style>
*{box-sizing:border-box}body{font-family:'Segoe UI',Arial,sans-serif;color:#1c2530;background:#f4f6f9;margin:0;padding:40px}
.sheet{max-width:820px;margin:0 auto;background:#fff;border-radius:14px;box-shadow:0 8px 40px rgba(20,30,50,.10);overflow:hidden}
header{background:linear-gradient(135deg,#1a0b2e,#3a1d5e);color:#fff;padding:28px 36px;display:flex;justify-content:space-between;align-items:center}
header h1{margin:0;font-size:24px;letter-spacing:.5px}header h1 span{color:#c46bff}
header .sub{font-size:12px;opacity:.7;margin-top:4px}.ts{font-size:11px;opacity:.6;text-align:right}
.hero{display:flex;gap:32px;padding:34px 36px;align-items:center;border-bottom:1px solid #e7ebf0}
.score{font-size:74px;font-weight:700;line-height:1;color:${vcol}}.score small{font-size:24px}
.verdict{display:inline-block;padding:8px 16px;border-radius:8px;font-weight:600;font-size:14px;color:${vcol};background:${vcol}1a;margin-bottom:10px}
.conf{font-size:13px;color:#5d6b7e}
h2{font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:#8595a8;margin:30px 36px 14px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:0 36px}
.m{display:flex;justify-content:space-between;padding:12px 14px;background:#f7f9fc;border:1px solid #eaeef4;border-radius:8px}
.ml{color:#5d6b7e;font-size:13px}.mv{font-weight:700;font-size:15px}
.cats{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:0 36px}
.c{text-align:center;padding:12px 6px;background:#f7f9fc;border:1px solid #eaeef4;border-radius:8px}
.cl{display:block;font-size:10px;color:#8595a8;letter-spacing:.5px}.cv{display:block;font-size:22px;font-weight:700;margin-top:4px}
table{width:calc(100% - 72px);margin:0 36px;border-collapse:collapse}td{padding:6px 4px;font-size:13px;vertical-align:middle}
td.sig{color:#3a4658;width:48%}td.track{width:42%;background:#eaeef4;border-radius:4px}
td.track span{display:block;height:7px;border-radius:4px}td.pct{text-align:right;font-weight:600;color:#5d6b7e;width:10%}
footer{margin-top:34px;padding:18px 36px;background:#f7f9fc;border-top:1px solid #e7ebf0;font-size:11px;color:#8595a8;display:flex;justify-content:space-between}
.note{margin:24px 36px;padding:14px 16px;background:#fff8e6;border:1px solid #f3e3b3;border-radius:8px;font-size:12px;color:#7a6a30}
@media print{body{background:#fff;padding:0}.sheet{box-shadow:none}}
</style></head><body><div class="sheet">
<header><div><h1>Jo<span>Di</span> · Informe de análisis</h1>
<div class="sub">Detector de contenido generado por inteligencia artificial · Web</div></div>
<div class="ts">Generado<br>${ts}</div></header>
<div class="hero"><div class="score">${score}<small>%</small></div>
<div><div class="verdict">${escapeHtml(verdict)}</div>
<div class="conf">Confianza del análisis: <b>${r.confidence}%</b> · ${r.word_count.toLocaleString("es")} palabras · ${r.sentence_count} oraciones</div></div></div>
<h2>Métricas del documento</h2><div class="grid">${metricCells}</div>
<h2>Frases detectadas por categoría</h2><div class="cats">${catCells}</div>
<h2>Señales que sugieren origen artificial</h2><table>${barRows(ia)}</table>
<h2>Rasgos humanos (reducen el score)</h2><table>${barRows(hu, true)}</table>
<div class="note"><b>Nota metodológica.</b> Este informe es una estimación estadística basada en
patrones léxicos y estructurales. No constituye prueba concluyente de autoría; debe interpretarse
junto con el juicio del evaluador.</div>
<footer><span>JoDi · Motor de análisis lingüístico (versión web)</span>
<span>Análisis ejecutado localmente en el navegador</span></footer>
</div></body></html>`;
}

/* ─────────────── Lista de stopwords (504, NLTK es+en) ─────────────── */
function STOPWORDS_LIST(){ return ["a","about","above","after","again","against","ain","al","algo","algunas","algunos","all","am","an","and","ante","antes","any","are","aren","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can","como","con","contra","couldn","couldn't","cual","cuando","d","de","del","desde","did","didn","didn't","do","does","doesn","doesn't","doing","don","don't","donde","down","durante","during","e","each","el","ella","ellas","ellos","en","entre","era","erais","eran","eras","eres","es","esa","esas","ese","eso","esos","esta","estaba","estabais","estaban","estabas","estad","estada","estadas","estado","estados","estamos","estando","estar","estaremos","estará","estarán","estarás","estaré","estaréis","estaría","estaríais","estaríamos","estarían","estarías","estas","este","estemos","esto","estos","estoy","estuve","estuviera","estuvierais","estuvieran","estuvieras","estuvieron","estuviese","estuvieseis","estuviesen","estuvieses","estuvimos","estuviste","estuvisteis","estuviéramos","estuviésemos","estuvo","está","estábamos","estáis","están","estás","esté","estéis","estén","estés","few","for","from","fue","fuera","fuerais","fueran","fueras","fueron","fuese","fueseis","fuesen","fueses","fui","fuimos","fuiste","fuisteis","further","fuéramos","fuésemos","ha","habida","habidas","habido","habidos","habiendo","habremos","habrá","habrán","habrás","habré","habréis","habría","habríais","habríamos","habrían","habrías","habéis","había","habíais","habíamos","habían","habías","had","hadn","hadn't","han","has","hasn","hasn't","hasta","have","haven","haven't","having","hay","haya","hayamos","hayan","hayas","hayáis","he","he'd","he'll","he's","hemos","her","here","hers","herself","him","himself","his","how","hube","hubiera","hubierais","hubieran","hubieras","hubieron","hubiese","hubieseis","hubiesen","hubieses","hubimos","hubiste","hubisteis","hubiéramos","hubiésemos","hubo","i","i'd","i'll","i'm","i've","if","in","into","is","isn","isn't","it","it'd","it'll","it's","its","itself","just","la","las","le","les","ll","lo","los","m","ma","me","mi","mightn","mightn't","mis","more","most","mucho","muchos","mustn","mustn't","muy","my","myself","más","mí","mía","mías","mío","míos","nada","needn","needn't","ni","no","nor","nos","nosotras","nosotros","not","now","nuestra","nuestras","nuestro","nuestros","o","of","off","on","once","only","or","os","other","otra","otras","otro","otros","our","ours","ourselves","out","over","own","para","pero","poco","por","porque","que","quien","quienes","qué","re","s","same","se","sea","seamos","sean","seas","sentid","sentida","sentidas","sentido","sentidos","seremos","será","serán","serás","seré","seréis","sería","seríais","seríamos","serían","serías","seáis","shan","shan't","she","she'd","she'll","she's","should","should've","shouldn","shouldn't","siente","sin","sintiendo","so","sobre","sois","some","somos","son","soy","su","such","sus","suya","suyas","suyo","suyos","sí","t","también","tanto","te","tendremos","tendrá","tendrán","tendrás","tendré","tendréis","tendría","tendríais","tendríamos","tendrían","tendrías","tened","tenemos","tenga","tengamos","tengan","tengas","tengo","tengáis","tenida","tenidas","tenido","tenidos","teniendo","tenéis","tenía","teníais","teníamos","tenían","tenías","than","that","that'll","the","their","theirs","them","themselves","then","there","these","they","they'd","they'll","they're","they've","this","those","through","ti","tiene","tienen","tienes","to","todo","todos","too","tu","tus","tuve","tuviera","tuvierais","tuvieran","tuvieras","tuvieron","tuviese","tuvieseis","tuviesen","tuvieses","tuvimos","tuviste","tuvisteis","tuviéramos","tuviésemos","tuvo","tuya","tuyas","tuyo","tuyos","tú","un","una","under","uno","unos","until","up","ve","very","vosotras","vosotros","vuestra","vuestras","vuestro","vuestros","was","wasn","wasn't","we","we'd","we'll","we're","we've","were","weren","weren't","what","when","where","which","while","who","whom","why","will","with","won","won't","wouldn","wouldn't","y","ya","yo","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves","él","éramos"]; }

/* ─────────────── Export ─────────────── */
global.JoDiEngine = {
  analyzeText,
  buildHtmlReport,
  verdictFor,
  status: { spacy:false, nltk:false, local:true },
};

})(window);
