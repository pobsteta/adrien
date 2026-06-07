/* Le Terminal Économies — barre latérale rétractable (façon YouTube).
   Aucune dépendance. L'état (ouvert/rétracté) est mémorisé entre les pages.

   Le corps porte la classe `sb-toggled` qui *inverse* l'état par défaut :
   - sur grand écran, la barre est ouverte par défaut ; `sb-toggled` la rétracte ;
   - sur mobile, elle est masquée par défaut ; `sb-toggled` l'ouvre en surimpression.
*/
(function () {
  "use strict";
  var KEY = "lte_sidebar";
  var body = document.body;

  // Restaure l'état mémorisé (uniquement utile sur grand écran).
  try {
    if (localStorage.getItem(KEY) === "toggled") {
      body.classList.add("sb-toggled");
    }
  } catch (e) { /* localStorage indisponible : on ignore */ }

  function setToggled(on) {
    body.classList.toggle("sb-toggled", on);
    try {
      localStorage.setItem(KEY, on ? "toggled" : "open");
    } catch (e) { /* ignore */ }
  }

  var toggle = document.getElementById("navToggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      setToggled(!body.classList.contains("sb-toggled"));
    });
  }

  // Sur mobile, un clic sur le fond sombre referme la barre.
  var backdrop = document.getElementById("navBackdrop");
  if (backdrop) {
    backdrop.addEventListener("click", function () { setToggled(false); });
  }

  // Sur mobile, choisir une section referme la barre pour révéler le contenu.
  var sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.addEventListener("click", function (ev) {
      var link = ev.target.closest("a[href*='#']");
      if (link && window.matchMedia("(max-width: 900px)").matches) {
        setToggled(false);
      }
    });
  }
})();

/* Bascule de langue FR ⇄ EN, sans rechargement ni service externe.
   - [data-en]   : éléments à texte unique ; l'original FR est mémorisé dans
                   data-fr au premier passage, puis on alterne innerHTML.
   - .js-term    : termes dynamiques (zones, libellés de menu) traduits via un
                   petit dictionnaire.
   - .js-date    : dates ; on traduit les noms de jours/mois et « à » → « at ».
   L'état est mémorisé dans localStorage et appliqué dès le chargement. */
(function () {
  "use strict";
  var KEY = "lte_lang";
  var btn = document.getElementById("langToggle");

  var TERMS = {
    "Amériques": "Americas", "Asie": "Asia", "Afrique": "Africa",
    "Océanie": "Oceania", "Europe": "Europe", "Institutions": "Institutions",
    "International": "International", "France": "France", "Marchés": "Markets", "Direct": "Live",
    "À la une": "Front page", "Flash": "Flash", "La sélection": "The selection"
  };
  var DAYS = {
    "lundi": "Monday", "mardi": "Tuesday", "mercredi": "Wednesday",
    "jeudi": "Thursday", "vendredi": "Friday", "samedi": "Saturday",
    "dimanche": "Sunday"
  };
  var MONTHS = {
    "janvier": "January", "février": "February", "mars": "March",
    "avril": "April", "mai": "May", "juin": "June", "juillet": "July",
    "août": "August", "septembre": "September", "octobre": "October",
    "novembre": "November", "décembre": "December"
  };

  function translateDate(t) {
    var out = t;
    Object.keys(DAYS).forEach(function (k) { out = out.replace(k, DAYS[k]); });
    Object.keys(MONTHS).forEach(function (k) { out = out.replace(k, MONTHS[k]); });
    return out.replace(" à ", " at ");
  }

  function apply(en) {
    document.documentElement.lang = en ? "en" : "fr";

    document.querySelectorAll("[data-en]").forEach(function (el) {
      if (el.getAttribute("data-fr") === null) {
        el.setAttribute("data-fr", el.innerHTML);
      }
      el.innerHTML = en ? el.getAttribute("data-en") : el.getAttribute("data-fr");
    });

    document.querySelectorAll(".js-term").forEach(function (el) {
      if (el.getAttribute("data-fr") === null) {
        el.setAttribute("data-fr", el.textContent.trim());
      }
      var fr = el.getAttribute("data-fr");
      el.textContent = en ? (TERMS[fr] || fr) : fr;
    });

    document.querySelectorAll(".js-date").forEach(function (el) {
      if (el.getAttribute("data-fr") === null) {
        el.setAttribute("data-fr", el.textContent);
      }
      var fr = el.getAttribute("data-fr");
      el.textContent = en ? translateDate(fr) : fr;
    });

    if (btn) {
      var label = btn.querySelector(".lang__label");
      if (label) label.textContent = en ? "FR" : "EN";
      btn.setAttribute("aria-pressed", en ? "true" : "false");
    }
  }

  var saved = "fr";
  try { saved = localStorage.getItem(KEY) || "fr"; } catch (e) { /* ignore */ }
  apply(saved === "en");

  if (btn) {
    btn.addEventListener("click", function () {
      var en = document.documentElement.lang !== "en";  // bascule
      apply(en);
      try { localStorage.setItem(KEY, en ? "en" : "fr"); } catch (e) { /* ignore */ }
    });
  }
})();

/* Horloge « live » : date + heure réelles à côté du badge LIVE, rafraîchies
   chaque seconde. Le format suit la langue courante (FR ⇄ EN). */
(function () {
  "use strict";
  var el = document.getElementById("liveClock");
  if (!el) return;

  function tick() {
    var loc = document.documentElement.lang === "en" ? "en-GB" : "fr-FR";
    var now = new Date();
    var d = now.toLocaleDateString(loc, { weekday: "short", day: "numeric", month: "short" });
    var t = now.toLocaleTimeString(loc, { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
    el.textContent = d + " · " + t;
  }

  tick();
  setInterval(tick, 1000);
})();

/* Graphique d'ambiance de l'accueil : on remplace la courbe décorative par
   les VRAIES valeurs de l'EUR/USD (taux de référence BCE, ~6 mois), via l'API
   gratuite Frankfurter (sans clé, CORS). Si le réseau échoue, on garde le
   visuel décoratif d'origine — la page reste parfaite hors-ligne. */
(function () {
  "use strict";
  var line = document.getElementById("ig-line-path");
  var area = document.getElementById("ig-area-path");
  if (!line || !area) return;            // présent uniquement sur l'accueil

  var W = 360, TOP = 44, BOTTOM = 180, FLOOR = 240;

  function iso(d) { return d.toISOString().slice(0, 10); }
  function frFixed(n, dec) {
    return n.toLocaleString("fr-FR",
      { minimumFractionDigits: dec, maximumFractionDigits: dec });
  }

  var end = new Date();
  var start = new Date();
  start.setDate(start.getDate() - 182);
  var url = "https://api.frankfurter.app/" + iso(start) + ".." + iso(end) +
            "?from=EUR&to=USD";

  fetch(url).then(function (r) { return r.json(); }).then(function (data) {
    var rates = data && data.rates ? data.rates : {};
    var dates = Object.keys(rates).sort();
    var vals = dates.map(function (d) { return rates[d].USD; })
                    .filter(function (v) { return typeof v === "number"; });
    if (vals.length < 2) return;

    var min = Math.min.apply(null, vals);
    var max = Math.max.apply(null, vals);
    var span = (max - min) || 1;

    var pts = vals.map(function (v, i) {
      var x = (i / (vals.length - 1)) * W;
      var y = BOTTOM - ((v - min) / span) * (BOTTOM - TOP);
      return [x, y];
    });

    var dLine = "M" + pts.map(function (p) {
      return p[0].toFixed(1) + "," + p[1].toFixed(1);
    }).join(" L");
    line.setAttribute("d", dLine);
    area.setAttribute("d", dLine + " L" + W + "," + FLOOR + " L0," + FLOOR + " Z");

    // Repositionne le point lumineux de fin de courbe.
    var last = pts[pts.length - 1];
    var dot = document.getElementById("ig-dot");
    var halo = document.getElementById("ig-dot-halo");
    if (dot) { dot.setAttribute("cx", last[0].toFixed(1)); dot.setAttribute("cy", last[1].toFixed(1)); }
    if (halo) { halo.setAttribute("cx", last[0].toFixed(1)); halo.setAttribute("cy", last[1].toFixed(1)); }

    // Les barres décoratives n'ont plus de sens face à des données réelles.
    var bars = document.getElementById("ig-bars");
    if (bars) bars.style.display = "none";

    // Badges : variation sur la période + dernière valeur réelle.
    var first = vals[0], lastV = vals[vals.length - 1];
    var chg = ((lastV - first) / first) * 100;
    var up = chg >= 0;
    var trend = document.getElementById("ig-trend");
    if (trend) {
      trend.textContent = (up ? "▲ +" : "▼ ") + frFixed(chg, 2) + " %";
      trend.classList.toggle("up", up);
      trend.classList.toggle("down", !up);
    }
    var rate = document.getElementById("ig-rate");
    if (rate) rate.textContent = "1 € = " + frFixed(lastV, 4) + " $";
  }).catch(function () { /* hors-ligne : on garde le visuel décoratif */ });
})();
