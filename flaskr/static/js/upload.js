updateList = function() {
    var input = document.getElementById('image');
    var output = document.getElementById('list');
    var children = "";
    for (var i = 0; i < input.files.length; ++i) {
        children += '<li>' + input.files.item(i).name + '</li>';
    }
    output.innerHTML = '<ul>'+children+'</ul>';
}

submit = function() {
  window.location.href = "{{ url_for('home.do_upload') }}"
}

function off() {
  document.getElementById("post-overlay").style.display = "none";
}

function login() {
  window.location.href = "{{ url_for('auth.login') }}"
}
