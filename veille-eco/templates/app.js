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
