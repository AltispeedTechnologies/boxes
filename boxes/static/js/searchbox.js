document.getElementById("filter_select").addEventListener("change", function() {
  var selectedFilter = this.value;
  var searchInputContainer = document.getElementById("search_input_container");
  var stateSelectContainer = document.getElementById("state_select_container");
  searchInputContainer.classList.toggle("d-none", selectedFilter === "current_state");
  stateSelectContainer.classList.toggle("d-none", selectedFilter !== "current_state");

  // Disable hidden form elements
  var hiddenFormElements = stateSelectContainer.querySelectorAll('select, input');
  hiddenFormElements.forEach(function(element) {
    element.disabled = selectedFilter !== "current_state";
  });
});
