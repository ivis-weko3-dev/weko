// require(["jquery", "bootstrap"], function() {});
$(document).ready(function () {
  initschema = {
        type: "object",
        properties: {},
        required: []
  }
  url_update_schema = '/admin/itemtypes/properties';
  element = document.getElementById('new_option');
  var editor = new JSONSchemaEditor(element, {
    startval: initschema,
    editor: true
  });
  let currentselected = 0;
  $('#previews').on('click', function(){
    schema = editor.getValue();
    forms = editor.exportForm();
    removeCurrentEnum(schema.properties);
    $('#schema_json').val(JSON.stringify(schema, null, 4));
    $('#form1_json').val(JSON.stringify(forms.form, null, 4));
    $('#form2_json').val(JSON.stringify(forms.forms, null, 4));
  });
  $('#sending').on('click', function(){
    let prop_name = $('#property_name').val();
    if(prop_name.length == 0) {
      $('#property_name').focus();
      $('#property_name').parent().addClass('has-error');
      return;
    }
    $('#property_name').parent().removeClass('has-error');
    let data = {
      name: $('#property_name').val(),
      schema: JSON.parse($('#schema_json').val()),
      form1: JSON.parse($('#form1_json').val()),
      form2: JSON.parse($('#form2_json').val())
    }
    send(url_update_schema, data);
  });

  function removeCurrentEnum(properties) {
    Object.keys(properties).forEach(function(key) {
      let subItem = properties[key];
      if (subItem.hasOwnProperty('currentEnum')) {
        delete subItem['currentEnum'];
      }
    })
  }

  function send(url, data){
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function(data,textStatus){
        $('.modal-body').text(data.msg);
        $('#myModal').modal('show');
      },
      error: function(textStatus,errorThrown){
        $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
        $('#myModal').modal('show');
      }
    });
  }

  $('#item-type-lists').on('click', function(){
    $('.pulldown').show();
    $('.failed').hide()
    $('.option').each(function() {
        $(this).show();
    });
    $(this).val("");
    const text = $('#search-keyword').text();
    $(this).attr("placeholder",text);
  });

  $('#item-type-lists').on('input', function(){
    $('.failed').hide();
    const filter = $(this).val().toLowerCase();
    $('.option').each(function() {
    if($(this).data('name').toLowerCase().includes(filter)) {
      $(this).show();
    }else{
      $(this).hide();
    }
    });
    if ($('.option:visible').length === 0) {
      $('.failed').show();
    }
    currentselected = 0;
  });



  $('.option').on('click', function(){
    selectelement($(this).data('id'));
  });
  
  // create from json data
  $('#rebuild').on('click', function(){
    schema_json_val = $('#schema_json').val();
    if(schema_json_val.length > 0) {
      schema_json = null;
      schema_json = JSON.parse(schema_json_val);
      editor.setValue({
        startval: schema_json,
        editor: true
      });
    }
  });

  $("#item-type-lists").keydown(function(e) {
  const v = $('.option:visible');
  v.removeClass('selected');
	if (e.key === "ArrowUp"){
    if(currentselected > 0){
      currentselected--;
    }
		v.eq(currentselected).addClass('selected')
	}
  else if (e.key === "ArrowDown"){
    if(currentselected < v.length -1){
      currentselected++;
    }
    v.eq(currentselected).addClass('selected')
   }
  else if (e.key === "Enter"){
    selectelement(v.eq(currentselected).data('id'));
  }

  v.eq(currentselected)[0].scrollIntoView({behavior:'smooth', block: 'nearest'});
  });

  $(".option").hover(function(e){
   const v = $('.option:visible');
   v.removeClass('selected');
  });
  
  function selectelement(id){
    url = '/admin/itemtypes/properties/' + id;
    if(id) {
      $.get(url, function(data, status){
        url_update_schema = '/admin/itemtypes/properties/' + data.id;
        $('#property_name').val(data.name);
        $('#schema_json').val(JSON.stringify(data.schema, null, 4));
        $('#form1_json').val(JSON.stringify(data.form, null, 4));
        $('#form2_json').val(JSON.stringify(data.forms, null, 4));
        editor.setValue({
          startval: data.schema,
          editor: true
        });
        $('#item-type-lists').val(data.name)
    });
    } else {
    url_update_schema = '/admin/itemtypes/properties';
      $('#property_name').val('');
      $('#schema_json').val('');
      $('#form1_json').val('');
      $('#form2_json').val('');
      editor.setValue({
        startval: initschema,
        editor: true
      });
    }
     $('.option').each(function() {
        $(this).hide();
    });
    $('.pulldown').hide()
    currentselected = 0;
  }

});



$(document).on('click', function(e) {
    if (!$(e.target).closest('#item-type-lists').length) {
      $('.option').each(function() {
      $(this).hide();
      $('.pulldown').hide()
    });
      if($('#item-type-lists').val() == "") {
        const text = $('#please-select').text();
        $('#item-type-lists').attr("placeholder",text);
      }
    }
});
