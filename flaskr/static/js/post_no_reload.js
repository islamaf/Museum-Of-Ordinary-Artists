$(document).on('submit', '#post-form', function(e){

  $.ajax({
    type:'post',
    url:'/submit_post',
    contentType: 'application/json;charset=UTF-8',
    data:{
      link: $("link").val()
    },
    success:function(){
      alert('saved');
    },
    error : function(xhr) {
      console.log(xhr);
  	}
  });
  console.log("done")
  e.preventDefault();
});
