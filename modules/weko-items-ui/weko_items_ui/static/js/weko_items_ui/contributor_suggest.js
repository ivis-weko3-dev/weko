var username_arr = [];
var email_arr = [];
var filter = {
  filter_username: "",
  filter_email: ''
}
/**
 * Map storing the candidate suggestion lists for each input element by its ID.
 * @type {Map<string, Array<string>>} */
const suggestState = new Map(); // inputId -> candidates array

/**
 * Store the candidate suggestion list for a given input in the shared
 * suggestState cache, replacing any previously stored candidates
 * @param  {string} inputId    The id of the input the candidates belong to
 * @param  {Array}  candidates The candidate strings to store
 */
function updateSuggestState(inputId, candidates) {
  suggestState.set(inputId, candidates);
}

/**
 * Close every open autocomplete dropdown in the document, except the one
 * owned by the input that was clicked (if any); removes the matching
 * ".autocomplete-list" elements from the DOM
 * @param {HTMLElement} [elmnt] The element that triggered the close (its own list is left open)
 */
function closeAllLists(elmnt) {
  var lists = document.getElementsByClassName("autocomplete-items");
  for (var list of Array.from(lists).reverse()) {
    var ownerInputId = list.id.slice(0, -("autocomplete-list".length));
    var clickedOwnerInput = elmnt && elmnt.id === ownerInputId;
    if (elmnt !== list && !clickedOwnerInput) {
      list.parentNode.removeChild(list);
    }
  }
}

/*execute a function when someone clicks in the document
  (registered once at script load, not once per initAutocomplete() call):*/
document.addEventListener("click", function (e) {
  closeAllLists(e.target);
});

var contributorSuggestFocus = new Map(); // inputId -> currentFocus (arrow-key selection index)

/**
 * Remove only the given input's own autocomplete list element (if present),
 * leaving any autocomplete list currently open on other inputs untouched
 * @param {HTMLElement} inp The input whose own autocomplete list should be removed
 */
function removeOwnAutocompleteList(inp) {
  var ownList = document.getElementById(inp.id + "autocomplete-list");
  if (ownList) {
    ownList.remove();
  }
}

/**
 * Rebuild and render the autocomplete dropdown for the given input from the
 * candidates currently stored for it in suggestState, filtered by prefix
 * match against the input's current value; each item's click handler fills
 * the input and triggers get_autofill_data(). Appends a count footer for the
 * number of rendered matches. Performs no Ajax request itself; only reads
 * from suggestState/contributorSuggestCache and writes to
 * contributorSuggestFocus and the DOM.
 * @param  {HTMLElement}   inp The input to render the autocomplete list for
 * @return {boolean | undefined} false when the input has no value (nothing rendered)
 */
function renderAutocompleteList(inp) {
  var arr = suggestState.get(inp.id) || [];
  var form_share_other_user, autocomplete_scroll, val = inp.value;
  var mode = inp.id;
  removeOwnAutocompleteList(inp);
  if (!val) {
    return false;
  }
  contributorSuggestFocus.set(inp.id, -1);
  form_share_other_user = document.createElement("div");
  form_share_other_user.setAttribute("id", inp.id + "autocomplete-list");
  form_share_other_user.setAttribute("class", "autocomplete-items");
  inp.parentNode.appendChild(form_share_other_user);

  autocomplete_scroll = document.createElement("div");
  autocomplete_scroll.setAttribute("class", "autocomplete-scroll");
  form_share_other_user.appendChild(autocomplete_scroll);

  // candidates that start with the same letters as the text field value:
  var matches = arr.filter((candidate) =>
    candidate.slice(0, val.length).toUpperCase() === val.toUpperCase()
  );

  matches.forEach((candidate) => {
    var item = document.createElement("div");
    item.classList.add("autocomplete-suggest-item");

    // make the matching letters bold:
    var strongEl = document.createElement("strong");
    strongEl.textContent = candidate.slice(0, val.length);
    item.appendChild(strongEl);
    item.appendChild(document.createTextNode(candidate.slice(val.length)));

    // hold the current candidate's value for the click handler below:
    var hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.value = candidate;
    item.appendChild(hiddenInput);

    // execute a function when someone clicks on the item value (DIV element);
    // this must stay a regular function, since `this` needs to be the
    // clicked element, not the lexical `this` an arrow function would use:
    item.addEventListener('click', function (e) {
      // insert the value for the autocomplete text field:
      inp.value = this.getElementsByTagName("input")[0].value;
      if (mode.match('share_username')) {
        filter.filter_username = inp.value;
        // get exact user info contains username and email by username unique
        get_autofill_data(filter.filter_username, "", mode);
      } else if (mode.match('share_email')) {
        filter.filter_email = inp.value;
        // get exact user info contains username and email by email
        get_autofill_data('', filter.filter_email, mode);
      }
      closeAllLists();
    });

    autocomplete_scroll.appendChild(item);
  });

  var matchCount = matches.length;
  if (matchCount === 0) {
    var noResult = document.createElement("div");
    noResult.classList.add("autocomplete-suggest-item");

    var noResultText = document.createElement("p");
    noResultText.textContent = "No result found";
    noResult.appendChild(noResultText);

    var noResultInput = document.createElement("input");
    noResultInput.type = "hidden";
    noResultInput.value = "No results found";
    noResult.appendChild(noResultInput);

    autocomplete_scroll.appendChild(noResult);
  }

  var suggest_cache = (typeof contributorSuggestCache !== "undefined") ? contributorSuggestCache[inp.id] : null;
  if (suggest_cache) {
    var autocomplete_count = document.createElement("div");
    autocomplete_count.setAttribute("class", "autocomplete-count");
    // "N results" (exact count) when hasMore === false and val is a forward
    // extension of the cached query - the same condition
    // scheduleSuggestSearch() uses to skip the server, meaning matchCount is
    // the exact total; otherwise "N+ results" since matchCount is only a lower
    // bound (more matches may exist server-side).
    autocomplete_count.textContent =
      (suggest_cache.hasMore === false && val.indexOf(suggest_cache.query) === 0) ?
        CONTRIBUTOR_SUGGEST_COUNT_LABEL.replace('{}', matchCount) :
        CONTRIBUTOR_SUGGEST_COUNT_MORE_LABEL.replace('{}', matchCount);
    form_share_other_user.appendChild(autocomplete_count);
  }
}

/**
 * Register the "input" and "keydown" event listeners that drive the
 * autocomplete dropdown for the given input (guarded by
 * dataset.autocompleteInit so this runs only once per input). Re-renders
 * the list on input, and handles arrow-key/Enter navigation on keydown.
 * @param {HTMLElement} inp The input to wire up autocomplete behavior for
 */
function initAutocomplete(inp) {
  if (inp.dataset.autocompleteInit) return;
  inp.dataset.autocompleteInit = "true";

  inp.addEventListener("input", function (e) {
    closeAllLists(this);
    renderAutocompleteList(this);
  });
  inp.addEventListener("keydown", function (e) {
    var currentFocus = contributorSuggestFocus.has(this.id) ? contributorSuggestFocus.get(this.id) : -1;
    var x = document.getElementById(this.id + "autocomplete-list");
    if (x) {
      x = x.getElementsByClassName("autocomplete-suggest-item");
    }
    if (e.key === "ArrowDown") {
      /*If the arrow DOWN key is pressed,
      increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      currentFocus = addActive(x, currentFocus);
    } else if (e.key === "ArrowUp") {
      /*If the arrow UP key is pressed,
      decrease the currentFocus variable:*/
      currentFocus--;
      /*and and make the current item more visible:*/
      currentFocus = addActive(x, currentFocus);
    } else if (e.key === "Enter") {
      /*If the ENTER key is pressed, prevent the form from being submitted,*/
      e.preventDefault();
      if (currentFocus > -1) {
        /*and simulate a click on the "active" item:*/
        if (x) {
          x[currentFocus].click();
        }
      } else {
        let target_id = this.id.replace('share_email_', '').replace('share_username_', '');
        if (currentFocus == -1 && $("#share_username_"+target_id).val() != '') {
          if (x) {
            x[0].click();
          }
        }
      }
    }
    contributorSuggestFocus.set(this.id, currentFocus);
  });
}
/**
 * Mark the item at currentFocus as the "active" (highlighted) autocomplete
 * item, normalizing currentFocus so it wraps within the bounds of the list
 * (below the last item wraps to the first, above the first wraps to the
 * last), removes the "active" class from all other items, and scrolls the
 * newly active item into view
 * @param  {HTMLCollection} x            The current autocomplete item elements
 * @param  {number}         currentFocus The requested focus index (may be out of bounds)
 * @return {number}                      The normalized currentFocus index that was activated
 */
function addActive(x, currentFocus) {
  if (!x) return currentFocus;
  /*start by removing the "active" class on all items:*/
  removeActive(x);
  if (currentFocus >= x.length) currentFocus = 0;
  if (currentFocus < 0) currentFocus = (x.length - 1);
  /*add class "autocomplete-active":*/
  x[currentFocus].classList.add("autocomplete-active");
  x[currentFocus].scrollIntoView({ block: "nearest" });
  return currentFocus;
}
/**
 * Remove the "autocomplete-active" class from every item in the given
 * autocomplete item collection
 * @param {HTMLCollection} x The autocomplete item elements to clear
 */
function removeActive(x) {
  for (var item of x) {
    item.classList.remove("autocomplete-active");
  }
}

/**
 * Register the "input" event listener that triggers a debounced server-side
 * contributor suggestion search for the given input (guarded by a
 * dataset.contributorSuggestInit flag so the listener is attached only once
 * per input). Each keystroke calls scheduleSuggestSearch()
 * @param {HTMLElement} inp The input to wire up contributor suggestion search for
 */
function initContributorSuggest(inp) {
  if (inp.dataset.contributorSuggestInit) return;
  inp.dataset.contributorSuggestInit = "true";
  inp.addEventListener("input", function () {
    scheduleSuggestSearch(inp);
  });
}
/**
 * Timers for debouncing contributor suggestion lookups, keyed by input ID.
 * @type {Object<string, number>}
 */
var contributorSuggestTimers = {};
/**
 * Cache for contributor suggestion results, keyed by input ID.
 * @type {Object<string, { query: string, hasMore: boolean, count: number, limit: number }>}
 */
var contributorSuggestCache = {};

/**
 * Debounce contributor suggestion lookups for the given input: clears any
 * pending timer and schedules a new one after CONTRIBUTOR_SUGGEST_DEBOUNCE_MS.
 * An empty value clears the cache/suggestState and reinitializes the local
 * autocomplete listeners without contacting the server; a non-empty value
 * triggers fetchContributorSuggestions(), unless the cache already covers it
 * (see inline comment below).
 * @param {HTMLElement} inp The input to schedule a suggestion search for
 */
function scheduleSuggestSearch(inp) {
  if (contributorSuggestTimers[inp.id]) {
    clearTimeout(contributorSuggestTimers[inp.id]);
  }
  contributorSuggestTimers[inp.id] = setTimeout(function () {
    var value = inp.value;
    if (!value) {
      contributorSuggestCache[inp.id] = null;
      updateSuggestState(inp.id, []);
      initAutocomplete(inp);
      return;
    }
    var keyword = inp.id.indexOf("share_username") === 0 ? "username" : "email";
    var cache = contributorSuggestCache[inp.id];
    if (cache && cache.hasMore === false && value.indexOf(cache.query) === 0) {
      // The previous fetch already returned every match: skip the server
      // request and let the local prefix filter (in initAutocomplete()) handle it.
      return;
    }
    fetchContributorSuggestions(keyword, inp.id, value);
  }, CONTRIBUTOR_SUGGEST_DEBOUNCE_MS);
}

/**
 * Fetch contributor suggestion candidates from the server for the given
 * input and update the local caches with the response, then re-render the
 * dropdown if the input is still focused and its value still matches the
 * response (see inline comments below for the stale-response and spinner
 * handling). Shows a spinner while the request is in flight; on failure or
 * a server-reported error, hides the spinner and shows an error modal
 * instead.
 * @param {string} keyword Which suggestion source to query ("username" or "email")
 * @param {string} inputId The id of the input the suggestions are for
 * @param {string} query   The current input value to search for
 */
function fetchContributorSuggestions(keyword, inputId, query) {
  // inputId is either "share_username"/"share_email" (single-value fields,
  // e.g. edit.html) or "share_username_<rowId>"/"share_email_<rowId>"
  // (per-row fields, e.g. the iframe contributor list). Strip the base
  // prefix (with an optional trailing "_") to recover "" or "<rowId>" so
  // the same selector construction works for either naming scheme.
  var id = inputId.replace(/^share_username_?/, '').replace(/^share_email_?/, '');
  var suffix = id ? ("_" + id) : "";
  $("#id_spinners_" + keyword + suffix).css("display", "inline-block");

  $.ajax({
    url: '/api/items/get_search_data/' + keyword,
    method: "GET",
    data: { q: query },
    success: function (data, status) {
      $("#id_spinners_" + keyword + suffix).css("display", "none");
      if (data.error) {
        var modalcontent = "Some errors have occured!\nDetail:" + data.error;
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return;
      }
      var inputElement = document.getElementById(inputId);
      if (!inputElement || inputElement.value !== data.query) {
        // The input was removed (e.g. its contributor row was deleted), or
        // its value changed, while this request was in flight: discard the
        // now-stale response instead of overwriting newer candidates.
        return;
      }
      if (keyword === 'username') {
        username_arr = data.results;
      } else if (keyword === 'email') {
        email_arr = data.results;
      }
      contributorSuggestCache[inputId] = {
        query: data.query,
        hasMore: data.has_more,
        count: data.count,
        limit: data.results.length
      };
      updateSuggestState(inputId, data.results);
      if (document.activeElement !== inputElement) return;
      // initAutocomplete() only registers listeners once; safe to call
      // again here to guarantee they exist before re-rendering.
      initAutocomplete(inputElement);
      renderAutocompleteList(inputElement);
    },
    error: function (data, status) {
      $("#id_spinners_" + keyword + suffix).css("display", "none");
      var modalcontent = "Cannot connect to server!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    }
  });
}

/**
 * Fetch autofill data for the given username or email and populate the
 * corresponding fields in the form. If "mode" indicates a username field,
 * the email field is updated, and vice versa.
 * @param {string} keyword The type of data being provided ("username" or "email")
 * @param {string} data The value of the username or email to validate
 * @param {string} mode The id of the input field that triggered the autofill
 */
function get_autofill_data(keyword, data, mode) {
  // If autofill, "keyword" = email or username, and username, email have to fill to "data"
  // If validate, keyword = username, data = email
  let param = {
    username: "",
    email: ""
  }
  if (keyword == "username") {
    param.username = data;
  } else if (keyword == "email") {
    param.email = data;
  } else {
    param.username = keyword;
    param.email = data;
  }

  //get id
  let mode_id = mode.replace('share_username_', '').replace('share_email_', '');
  //Create request
  $.ajax({
    url: "/api/items/validate_user_info",
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    data: JSON.stringify(param),
    dataType: "json",
    success: function (data, status) {
      if (mode.match('share_username')) {
        $("#share_email_"+mode_id).val(data.results.email);
      } else if (mode.match('share_email')) {
        if (data.results.username) {
          $("#share_username_"+mode_id).val(data.results.username);
        } else {
          $("#share_username_"+mode_id).val("");
        }
      }
    },
    error: function (data, status) {
      var modalcontent = "Cannot connect to server!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    }
  });
}
/**
 * Handle the username field losing focus: clears the cached username_arr
 * suggestions and marks the corresponding email field as read-only
 * @param {string} share_username_id The id of the username input that lost focus
 */
function focusoutShareUsername(share_username_id) {
  username_arr = [];
  id = share_username_id.replace('share_username_', '');
  $("#share_email_" + id).prop('readonly', true);
}
/**
 * Handle the email field losing focus: clears the cached username_arr
 * suggestions and marks the corresponding username field as read-only
 * @param {string} share_email_id The id of the email input that lost focus
 */
function focusoutShareEmail(share_email_id) {
  username_arr = [];
  id = share_email_id.replace('share_email_', '');
  $("#share_username_" + id).prop('readonly', true);
}

/**
 * Remove a contributor row (an existing user's row via user_id, or a new
 * blank row via id_value) from the form, unless doing so would leave fewer
 * than 2 contributor rows, in which case an alert is shown instead
 * @param  {number|string} user_id    The existing user's id, or 0 for a new row
 * @param  {string}        [id_value] The trash icon's element id (used only when user_id is 0)
 * @return {boolean|undefined} false when removal is blocked by the minimum row requirement
 */
async function removeUser(user_id, id_value) {
  let parent_id;
  let email_id;
  if(user_id == 0) {
    id_value = id_value.replace('id_trash_0_', '');
    let id = parseInt(id_value);
    if (!isNaN(id)) {
      parent_id = `#contributor_new_row_${id}`;
      email_id = `#share_email_0_${id}`;
    }
  }else{
    parent_id = `#contributor_row_${user_id}`;
    email_id = `#share_email_${user_id}`;
  }

  // Newボタンで追加したユーザー情報
  let search_new_ids = $('[id^="contributor_new_row_"]');
  // 本アクティビティに登録済みユーザー情報
  let search_ids = $('[id^="contributor_row_"]');

  if(search_ids.length + search_new_ids.length < 2) {
    message = $("#min_user_required_error").val();
    alert(message);
    return false;
  }

  //削除実行
  $(parent_id).remove();
}

/**
 * Append a new, blank contributor row to the form by cloning the
 * "#contributor_new_row" template, renumbering its child element ids/names
 * with the next available sequence number (one past the highest existing
 * "contributor_new_row_<n>" id), and inserting it into the DOM after the
 * last existing new row (or after the template itself for the first row)
 */
function addUser() {
  let max_id = 0;
  let search_ids = $('[id^="contributor_new_row_"]');
  for(let idx=0; idx<search_ids.length; idx++) {
    let str = search_ids[idx].id.split('_');
    if(str.length < 4) {
      continue;
    }
    let no = parseInt(str[3]);
    if (no != NaN & no > max_id) {
      max_id = no;
    }
  }
  max_id += 1;

  let base_node = $("#contributor_new_row").clone(true);
  base_node.attr('id', `contributor_new_row_${max_id}`);
  base_node.css('display', 'block');
  base_node.find('#pd_username_0').attr('id', `pd_username_0_${max_id}`);
  base_node.find('#label_username_0').attr('id', `label_username_0_${max_id}`);
  base_node.find('#label_email_0').attr('id', `label_email_0_${max_id}`);
  base_node.find('#id_spinners_email_0').css('display', 'none');
  base_node.find('#id_owner_radio_0').attr('id', `id_owner_radio_0_${max_id}`);
  base_node.find('#share_username_0').attr('id', `share_username_0_${max_id}`);
  base_node.find('#id_spinners_username_0').attr('id', `id_spinners_username_0_${max_id}`);
  base_node.find('#share_email_0').attr('id', `share_email_0_${max_id}`);
  base_node.find('#share_email_0').attr('name', `share_email_0_${max_id}`);
  base_node.find('#id_trash_0').attr('id', `id_trash_0_${max_id}`);

  if (max_id == 1) {
    $("#contributor_new_row").after(base_node);
  }
  else{
    $(`#contributor_new_row_${max_id-1}`).after(base_node);
  }
  return;
}

/**
 * Toggle the visibility of the ".form_share_permission" elements based on
 * the selected share permission: hidden for "this_user", shown for
 * "other_user" (any other value is a no-op)
 * @param {string} value The selected share permission ("this_user" or "other_user")
 */
function handleSharePermission(value) {
  if (value == 'this_user') {
    $(".form_share_permission").css('display', 'none');
  } else if (value == 'other_user') {
    $(".form_share_permission").css('display', 'block');
  }
}
