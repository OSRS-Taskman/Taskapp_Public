$(window).on('load', function(){
    var frameSpeed = 1000,
        frameContainer = $('#frame-container'),
        frames = $('.frame',frameContainer ),
        frameCount = frames.length,
        messageContainer = $('#message-container'),
        messages = $('.message', messageContainer)
        messageCount = messages.length,
        t = null,
        start = $('#start'),
        showFrame = function (n){
        		if (n != frameCount){
            	return frames.hide().eq(n).show() && messages.hide().eq(n).show();

            }
            return frames.eq(frameCount).show() && messages.eq(messageCount).show();

        },
        nextFrame = function(){
        		if (index == frameCount){
            	stopFrames();
              showFrame(frameCount - 1);
            }
            else {
              showFrame(++index);
              t = setTimeout(nextFrame,frameSpeed);
            }

        },
        stopFrames = function(){
            clearInterval(t);
            index = 0;
        };
    frameContainer
    	start.on('click', nextFrame)
        stopFrames();
        showFrame(0);
});

$(document).on('click', '#start', function(){
  req = $.ajax({
    url : '/generate/',
    type : 'POST'
  })

  req.done(function(data){
    delay(function(){
        const message = document.getElementById("message_target");
        const image = document.getElementById("image_target");
        const imageLink = document.getElementById("taskImage");
        imageLink.href = data.link;
        imageLink.setAttribute('data-tip', data.tip);
        message.innerHTML = data.name;
        image.src = data.image;
        document.getElementById("start").disabled = true;
        document.getElementById("complete").disabled = false;
    }, 6000);
  });
});

$(document).on('click', '#complete', function(){
  req = $.ajax({
    url : '/complete/',
    type : 'POST'

  });
  req.done(function(data){
    location.reload();
  })
});


var delay = (function(){
  var timer = 0;
  return function(callback, ms) {
    clearTimeout (timer);
    timer = setTimeout(callback, ms);
  };
})();

// $(document).on('click', '#easy_generate', function(){
//   $('form').submit(false);
//   req = $.ajax({
//     url : '/generate_unofficial_easy/',
//     type : 'POST'
//   });
//   req.done(function(data){
//     const task = document.getElementById("easy_task")
//     const image = document.getElementById("easy_image")
//     const imagePreview = document.getElementById("easy_image_preview")
//     task.innerHTML = data.name
//     image.src = "/static/assets/" + data.image
//     imagePreview.src = "/static/assets/" + data.image

//   });
// });

$(document).on('click', '#generate_unofficial', function(){
  $('form').submit(false);
  let tier = this.name
  req = $.ajax({
    url : '/generate_unofficial/',
    type : 'POST',
    data : {tier : tier + 'Tasks'}
  });
  req.done(function(data){
    const task = document.getElementById(tier + "_task");
    const image = document.getElementById(tier + "_image");
    const imagePreview = document.getElementById(tier + "_image_preview");
    var imagePlaceholder = document.getElementById(tier + "_placeholder");
    if (!imagePlaceholder){
       imagePlaceholder = document.getElementById(tier + '_imageTask')
    }
    imagePlaceholder.setAttribute('data-tip', data.tip)
    imagePlaceholder.href = data.link
    imagePreview.name = data.name;
    task.innerHTML = data.name;
    if (data.image === 'Cake_of_guidance_detail.png') {
    image.src = '/static/assets/Cake_of_guidance_detail.png';
    imagePreview.src = '/static/assets/Cake_of_guidance_detail.png';
  } else {
    image.src = data.image;
    imagePreview.src = data.image;
  }
  });
});


$(document).on('click', '#complete_unofficial', function(){
  $('form').submit(false);
  tier = this.name

  req = $.ajax({
    url : '/complete_unofficial/',
    type : 'POST',
    data : {tier : tier + 'Tasks'}
  });
  req.done(function(data){
    const updatePercent = document.getElementById(tier + "Percent")
    const task = document.getElementById(tier + "_task");
    const image = document.getElementById(tier + "_image");
    const imagePreview = document.getElementById(tier + "_image_preview");
    var imagePlaceholder = document.getElementById(tier  + '_placeholder');
    if (!imagePlaceholder){
      imagePlaceholder = document.getElementById(tier + '_imageTask')
    }
    imagePlaceholder.setAttribute('data-tip', 'Generate a Task!')
    imagePlaceholder.href = '#'
    imagePreview.name = "";
    task.innerHTML = "You have no " + tier + " task!";
    image.src = "/static/assets/Cake_of_guidance_detail.png";
    imagePreview.src = "/static/assets/Cake_of_guidance_detail.png";
    updatePercent.innerHTML = data[tier] + '%'
  });
});

$(document).on('click', '#easy_complete', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/complete_unofficial_easy/',
    type : 'POST'
  });
  req.done(function(){
    const task = document.getElementById("easy_task");
    const image = document.getElementById("easy_image");
    const imagePreview = document.getElementById("easy_image_preview");
    const imageTip = document.getElementById("imageTask");
    task.innerHTML = "You have no easy task!";
    image.src = "/static/assets/Cake_of_guidance_detail.png";
    imagePreview.src = "/static/assets/Cake_of_guidance_detail.png";


  });
});

$(document).on('click', '#medium_generate', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/generate_unofficial_medium/',
    type : 'POST'

  });

});

$(document).on('click', '#medium_complete', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/complete_unofficial_medium/',
    type : 'POST'

  });

});


$(document).on('click', '#hard_generate', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/generate_unofficial_hard/',
    type : 'POST'

  });

});

$(document).on('click', '#hard_complete', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/complete_unofficial_hard/',
    type : 'POST'

  });

});


$(document).on('click', '#elite_generate', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/generate_unofficial_elite/',
    type : 'POST'

  });

});

$(document).on('click', '#elite_complete', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/complete_unofficial_elite/',
    type : 'POST'
  });

});


$(document).on('click', '#master_generate', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/generate_unofficial_master/',
    type : 'POST'
  });

});

$(document).on('click', '#master_complete', function(){
  $('form').submit(false);
  req = $.ajax({
    url : '/complete_unofficial_master/',
    type : 'POST'

  });

});

$(document).ready(function(){
  $('.square a').click(function(event){
    event.stopPropagation();
  });
});

$(document).ready(function(){
  $(document).on('click', '.updateButton', function(){
    if ($(this).data('type') === 'bossPets' || $(this).data('type') === 'skillPets' || $(this).data('type') === 'otherPets'){
      var tier = $(this).data('type');
      var updatePercent = document.getElementById("allPetsPercent")
    }
    else {
      var tier = $('#tier').data('tier');
      var updatePercent = document.getElementById(tier + "Percent")
    }
    var elementTarget = this;
    var parent = elementTarget.parentElement;



    $('form').submit(false);
    req = $.ajax({
      url :  '/update_completed/',
      type : 'POST',
      data : {id : this.id, tier : tier}
    });

    req.done(function(data){
      $(elementTarget).fadeOut(1000).fadeIn(1000);
      $(elementTarget).removeClass('updateButton').addClass('revertButton');
      $(parent).removeClass('incomplete-hover').addClass('complete-hover');
      parent.setAttribute('data-tooltip', 'Mark Incomplete');
      if (tier === 'bossPets' || tier === 'skillPets' || tier === 'otherPets'){
        updatePercent.innerHTML = data["allPets"] + '%';
      }
      else {
        updatePercent.innerHTML = data[tier] + '%';
      }

      for (const child of elementTarget.children) {
        if (child.tagName === 'DIV') {
          $(child).addClass('square-complete');
          $(child).removeClass('square-incomplete');
        }

        if (child.tagName === 'P'){
          $(child).addClass('complete');
          $(child).removeClass('incomplete');
        }
      }

    });
  });
});

$(document).ready(function(){
  $(document).on('click', '.revertButton', function(){
    if ($(this).data('type') === 'bossPets' || $(this).data('type') === 'skillPets' || $(this).data('type') === 'otherPets'){
      var tier = $(this).data('type');
      var updatePercent = document.getElementById("allPetsPercent")
    }
    else {
      var tier = $('#tier').data('tier');
      var updatePercent = document.getElementById(tier + "Percent")
    }
    var elementTarget = this;
    var parent = elementTarget.parentElement;


    $('form').submit(false);
    req = $.ajax({
      url :  '/revert_completed/',
      type : 'POST',
      data : {id : this.id, tier : tier}
    });

    req.done(function(data){
      $(elementTarget).fadeOut(1000).fadeIn(1000);
      $(elementTarget).removeClass('revertButton').addClass('updateButton');
      $(parent).removeClass('complete-hover').addClass('incomplete-hover');
      parent.setAttribute('data-tooltip', 'Mark Complete');
      if (tier === 'bossPets' || tier === 'skillPets' || tier === 'otherPets'){
        updatePercent.innerHTML = data["allPets"] + '%';
      }
      else {
        console.log(tier)
        updatePercent.innerHTML = data[tier] + '%';
      }

      for (const child of elementTarget.children) {
        if (child.tagName === 'DIV') {
          $(child).addClass('square-incomplete');
          $(child).removeClass('square-complete');
        }

        if (child.tagName === 'P'){
          $(child).addClass('incomplete');
          $(child).removeClass('complete');
        }
      }

    });
  });
});


$(document).ready(function(){
  $(document).on('click', '#rankCheckButton', function(){
    var input = document.getElementById('rankCheckInput');
    var username = input.value;
    var rcContent = document.getElementById('rankCheckContent');

    req = $.ajax({
      url : '/collectionlog_check/',
      type : 'POST',
      data : {username : username}
    });

    req.done(function(data) {
      $(rcContent).html(data)
    });
  });
});

$(document).ready(function(){
  $(document).on('click', '#importButton', function(){
    var input = document.getElementById('importInput');
    var username = input.value;
    var importConent = document.getElementById('importContent');

    req = $.ajax({
      url : '/collectionlog_import/',
      type : 'POST',
      data : {username : username}
    });

    req.done(function(data) {
      $(importConent).html(data)
    });
  });
});

$(document).ready(function(){
$('.task-image').mouseenter(function(){
  const tip = this.name;
  const targetElement = this.parentElement.parentElement.parentElement.parentElement;
  targetElement.setAttribute('data-tooltip', tip);
});

$('.task-image').mouseleave(function(){
  const targetElement = this.parentElement.parentElement.parentElement.parentElement;
  const classes = targetElement.classList;
  const elements = Array.from(classes)
  if (elements.includes("complete-hover")) {
    targetElement.setAttribute('data-tooltip', 'Mark Incomplete');
  }

  if (elements.includes("incomplete-hover")){
    targetElement.setAttribute('data-tooltip', 'Mark Complete');
  }

  if (elements.includes('current-task-hover')){
    targetElement.setAttribute('data-tooltip', 'Use Dashboard To Complete Task');
  }
});
});

$(document).ready(function(){
  $("#easy_image_preview").mouseenter(function(){
    target = $("#b");
    target.text(this.name);
    target.addClass("active-task-tooltip-hover");
  });

  $("#easy_image_preview").mouseleave(function(){
    target = $("#b");
    target.removeClass("active-task-tooltip-hover");
  });

  $("#medium_image_preview").mouseenter(function(){
    target = $("#b");
    target.text(this.name);
    target.addClass("active-task-tooltip-hover");
  });

  $("#medium_image_preview").mouseleave(function(){
    target = $("#b");
    target.removeClass("active-task-tooltip-hover");
  });

  $("#hard_image_preview").mouseenter(function(){
    target = $("#b");
    target.text(this.name);
    target.addClass("active-task-tooltip-hover");
  });

  $("#hard_image_preview").mouseleave(function(){
    target = $("#b");
    target.removeClass("active-task-tooltip-hover");
  });

  $("#elite_image_preview").mouseenter(function(){
    target = $("#b");
    target.text(this.name);
    target.addClass("active-task-tooltip-hover");
  });

  $("#elite_image_preview").mouseleave(function(){
    target = $("#b");
    target.removeClass("active-task-tooltip-hover");
  });

  $("#master_image_preview").mouseenter(function(){
    target = $("#b");
    target.text(this.name);
    target.addClass("active-task-tooltip-hover");
  });

  $("#master_image_preview").mouseleave(function(){
    target = $("#b");
    target.removeClass("active-task-tooltip-hover");
  });

});


$(document).on('click', '.missing-easy', function(){
  $('form').submit(false);
  console.log('click')
  var tasks = document.getElementsByClassName('li-easy');
  for (let i = 0; i < tasks.length; i++) {
    if (tasks[i].style.display == 'none') {
      tasks[i].style.display = 'block';
    }
    else {
      tasks[i].style.display = 'none';
    }

  }
});


$(document).on('click', '.missing-medium', function(){
  $('form').submit(false);
  console.log('click')
  var tasks = document.getElementsByClassName('li-medium');
  for (let i = 0; i < tasks.length; i++) {
    if (tasks[i].style.display == 'none') {
      tasks[i].style.display = 'block';
    }
    else {
      tasks[i].style.display = 'none';
    }

  }
});



$(document).on('click', '.missing-hard', function(){
  $('form').submit(false);
  console.log('click')
  var tasks = document.getElementsByClassName('li-hard');
  for (let i = 0; i < tasks.length; i++) {
    if (tasks[i].style.display == 'none') {
      tasks[i].style.display = 'block';
    }
    else {
      tasks[i].style.display = 'none';
    }

  }
});

$(document).on('click', '.missing-elite', function(){
  $('form').submit(false);
  console.log('click')
  var tasks = document.getElementsByClassName('li-elite');
  for (let i = 0; i < tasks.length; i++) {
    if (tasks[i].style.display == 'none') {
      tasks[i].style.display = 'block';
    }
    else {
      tasks[i].style.display = 'none';
    }

  }
});
