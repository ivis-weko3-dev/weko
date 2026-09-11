var username_arr = [];
var email_arr = [];
var filter = {
  filter_username: "",
  filter_email: ''
}
const suggestState = new Map(); // inputId -> candidates array

function updateSuggestState(inputId, candidates) {
  suggestState.set(inputId, candidates);
}

function closeAllLists(elmnt) {
  /*close all autocomplete lists in the document,
  except the one owned by the input that was clicked:*/
  var lists = document.getElementsByClassName("autocomplete-items");
  for (var i = lists.length - 1; i >= 0; i--) {
    var list = lists[i];
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

function initAutocomplete(inp) {
  if (inp.dataset.autocompleteInit) return;
  inp.dataset.autocompleteInit = "true";

  var currentFocus = -1;

  inp.addEventListener("input", function (e) {
    var arr = suggestState.get(this.id) || [];
    var form_share_other_user, autocomplete_scroll, droplist_show_other_user, i, val = this.value;
    var mode = this.id;
    var flag = false;
    closeAllLists();
    if (!val) {
      return false;
    }
    currentFocus = -1;
    form_share_other_user = document.createElement("div");
    form_share_other_user.setAttribute("id", this.id + "autocomplete-list");
    form_share_other_user.setAttribute("class", "autocomplete-items");
    this.parentNode.appendChild(form_share_other_user);

    autocomplete_scroll = document.createElement("div");
    autocomplete_scroll.setAttribute("class", "autocomplete-scroll");
    form_share_other_user.appendChild(autocomplete_scroll);

    /*for each item in the array...*/
    for (i = 0; i < arr.length; i++) {
      /*check if the item starts with the same letters as the text field value:*/
      if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
        /*create a DIV element for each matching element:*/
        droplist_show_other_user = document.createElement("div");
        droplist_show_other_user.classList.add("autocomplete-suggest-item");
        /*make the matching letters bold:*/
        droplist_show_other_user.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
        droplist_show_other_user.innerHTML += arr[i].substr(val.length);
        /*insert a input field that will hold the current array item's value:*/
        droplist_show_other_user.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";

        /*execute a function when someone clicks on the item value (DIV element):*/
        droplist_show_other_user.addEventListener('click', function (e) {
          /*insert the value for the autocomplete text field:*/
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

        autocomplete_scroll.appendChild(droplist_show_other_user);
        flag = true;
      }
    }
    if (flag == false) {
      if (autocomplete_scroll.children.length == 0) {
        droplist_show_other_user = document.createElement("div");
        droplist_show_other_user.classList.add("autocomplete-suggest-item");
        droplist_show_other_user.innerHTML = "<p>No result found" + "</p>";
        droplist_show_other_user.innerHTML += "<input type='hidden' value='No results found'>";
        autocomplete_scroll.appendChild(droplist_show_other_user);
      }
    }

    var suggest_cache = (typeof contributorSuggestCache !== "undefined") ? contributorSuggestCache[this.id] : null;
    if (suggest_cache) {
      var autocomplete_count = document.createElement("div");
      autocomplete_count.setAttribute("class", "autocomplete-count");
      autocomplete_count.textContent = suggest_cache.hasMore ?
        CONTRIBUTOR_SUGGEST_COUNT_MORE_LABEL.replace('{}', suggest_cache.limit) :
        CONTRIBUTOR_SUGGEST_COUNT_LABEL.replace('{}', suggest_cache.count);
      form_share_other_user.appendChild(autocomplete_count);
    }
  });
  inp.addEventListener("keydown", function (e) {
    var x = document.getElementById(this.id + "autocomplete-list");
    if (x) {
      x = x.getElementsByClassName("autocomplete-suggest-item");
    }
    if (e.keyCode == 40) {
      /*If the arrow DOWN key is pressed,
      increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 38) { //up
      /*If the arrow UP key is pressed,
      decrease the currentFocus variable:*/
      currentFocus--;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 13) {
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
  });
  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
    x[currentFocus].scrollIntoView({ block: "nearest" });
  }
  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }
}

function initContributorSuggest(inp) {
  if (inp.dataset.contributorSuggestInit) return;
  inp.dataset.contributorSuggestInit = "true";
  inp.addEventListener("input", function () {
    scheduleSuggestSearch(inp);
  });
}

var contributorSuggestTimers = {};
var contributorSuggestCache = {}; // inputId -> { query: string, hasMore: bool, count: number, limit: number }

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
      initAutocomplete(inputElement);
    },
    error: function (data, status) {
      $("#id_spinners_" + keyword + suffix).css("display", "none");
      var modalcontent = "Cannot connect to server!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    }
  });
}

get_autofill_data = function (keyword, data, mode) {
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
function focusoutShareUsername(share_username_id) {
  username_arr = [];
  id = share_username_id.replace('share_username_', '');
  $("#share_email_" + id).prop('readonly', true);
}
function focusoutShareEmail(share_email_id) {
  username_arr = [];
  id = share_email_id.replace('share_email_', '');
  $("#share_username_" + id).prop('readonly', true);
}

removeUser = async(user_id, id_value) => {
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

// append new row contributor
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

function handleSharePermission(value) {
  if (value == 'this_user') {
    $(".form_share_permission").css('display', 'none');
  } else if (value == 'other_user') {
    $(".form_share_permission").css('display', 'block');
  }
}
