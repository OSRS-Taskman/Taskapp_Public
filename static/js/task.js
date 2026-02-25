const SPECIAL_ROLL_USERNAMES = new Set(['shadukat', 'gerni shadu']);

function getCurrentUsername() {
  const profileLink = document.querySelector('a.profile');
  return profileLink ? profileLink.textContent.trim().toLowerCase() : '';
}

function isSpecialRollUser() {
  return SPECIAL_ROLL_USERNAMES.has(getCurrentUsername());
}

function isShaduKatUser() {
  return getCurrentUsername() === 'shadukat';
}

function getCookieValue(name) {
  const encodedName = `${encodeURIComponent(name)}=`;
  const cookies = document.cookie ? document.cookie.split(';') : [];
  for (let i = 0; i < cookies.length; i += 1) {
    const cookie = cookies[i].trim();
    if (cookie.indexOf(encodedName) === 0) {
      return decodeURIComponent(cookie.substring(encodedName.length));
    }
  }
  return null;
}

function shouldSkipRollAnimation() {
  return getCookieValue('skip_roll_animation') === 'true';
}

function shuffleArray(items) {
  const cloned = items.slice();
  for (let i = cloned.length - 1; i > 0; i -= 1) {
    const randomIndex = Math.floor(Math.random() * (i + 1));
    [cloned[i], cloned[randomIndex]] = [cloned[randomIndex], cloned[i]];
  }
  return cloned;
}

function ensureRollModal() {
  let modal = document.getElementById('taskRollModal');
  if (modal) {
    return modal;
  }

  modal = document.createElement('dialog');
  modal.id = 'taskRollModal';
  modal.className = 'task-roll-modal';
  modal.innerHTML = `
    <div class="task-roll-shell rsText">
      <div class="task-roll-title">Rolling Task</div>
      <div class="task-roll-content">
        <img id="taskRollModalImage" class="task-roll-image" src="/static/assets/Cake_of_guidance_detail.png" alt="Task roll image" />
        <p id="taskRollModalMessage" class="task-roll-message">Rolling...</p>
        <p id="taskRollModalSpecial" class="task-roll-special" hidden>Hi Youtube &lt;3 Gerni Task</p>
      </div>
      <div class="task-roll-actions">
        <button id="taskRollModalClose" class="task-roll-button" type="button">Continue</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  const closeButton = modal.querySelector('#taskRollModalClose');
  closeButton.addEventListener('click', () => {
    if (typeof modal.close === 'function') {
      modal.close();
    }
  });

  return modal;
}

function buildFallbackRollCandidates() {
  return [
    { name: 'Rolling...', image: '/static/assets/Cake_of_guidance_detail.png' },
    { name: 'Rolling...', image: '/static/assets/Tome_of_fire_(empty).png' },
    { name: 'Rolling...', image: '/static/assets/Cockatrice_head.png' },
    { name: 'Rolling...', image: '/static/assets/Dragon_sword.png' },
    { name: 'Rolling...', image: '/static/assets/Guilded_smile_flag.png' },
    { name: 'Rolling...', image: '/static/assets/Malediction_shard_2.png' }
  ];
}

function getOfficialRollCandidates() {
  const frameNodes = document.querySelectorAll('#frame-container .frame');
  const messageNodes = document.querySelectorAll('#message-container .message');
  const candidates = [];

  frameNodes.forEach((frameNode, index) => {
    const imageSrc = frameNode.getAttribute('src');
    const messageNode = messageNodes[index];
    const messageText = messageNode ? messageNode.textContent.trim() : 'Rolling...';
    if (imageSrc) {
      candidates.push({ name: messageText || 'Rolling...', image: imageSrc });
    }
  });

  return candidates.length > 0 ? candidates : buildFallbackRollCandidates();
}

function normalizeServerRollCandidates(serverCandidates) {
  if (!Array.isArray(serverCandidates)) {
    return [];
  }

  return serverCandidates
    .map((candidate) => ({
      name: candidate && candidate.name ? candidate.name : 'Rolling...',
      image: candidate && candidate.image ? candidate.image : '/static/assets/Cake_of_guidance_detail.png'
    }))
    .filter((candidate) => Boolean(candidate.image));
}

function resolveTaskImageSource(imageValue) {
  if (!imageValue) {
    return '/static/assets/Cake_of_guidance_detail.png';
  }
  if (imageValue.startsWith('http://') || imageValue.startsWith('https://') || imageValue.startsWith('/static/')) {
    return imageValue;
  }
  return `/static/assets/${imageValue}`;
}

function rollTaskModal(options) {
  const {
    finalName,
    finalImage,
    instant = false,
    showSpecialMessage = false,
    candidates = []
  } = options;

  return new Promise((resolve) => {
    const modal = ensureRollModal();
    const imageNode = modal.querySelector('#taskRollModalImage');
    const messageNode = modal.querySelector('#taskRollModalMessage');
    const specialNode = modal.querySelector('#taskRollModalSpecial');
    const closeButton = modal.querySelector('#taskRollModalClose');

    let settled = false;

    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      closeButton.onclick = null;
      resolve();
    };

    closeButton.onclick = () => {
      if (typeof modal.close === 'function') {
        modal.close();
      }
      finish();
    };

    if (typeof modal.showModal === 'function') {
      modal.showModal();
    }

    const finalImageSource = resolveTaskImageSource(finalImage);
    specialNode.hidden = !showSpecialMessage;

    if (instant) {
      imageNode.src = finalImageSource;
      messageNode.textContent = finalName;
      closeButton.disabled = false;
      return;
    }

    const baseCandidates = candidates.length > 0 ? candidates : buildFallbackRollCandidates();
    const randomizedCandidates = shuffleArray(baseCandidates).concat([{ name: finalName, image: finalImageSource }]);
    let pointer = 0;
    closeButton.disabled = true;

    const intervalId = window.setInterval(() => {
      const nextCandidate = randomizedCandidates[pointer];
      imageNode.src = resolveTaskImageSource(nextCandidate.image);
      messageNode.textContent = nextCandidate.name || 'Rolling...';
      pointer += 1;

      if (pointer >= randomizedCandidates.length) {
        window.clearInterval(intervalId);
        imageNode.src = finalImageSource;
        messageNode.textContent = finalName;
        closeButton.disabled = false;
      }
    }, 120);
  });
}

$(document).on('click', '#start', function(){
  req = $.ajax({
    url : '/generate/',
    type : 'POST'
  });

  req.done(async function(data){
    const serverCandidates = normalizeServerRollCandidates(data.rollCandidates);
    const rollCandidates = serverCandidates.length > 0 ? serverCandidates : getOfficialRollCandidates();
    await rollTaskModal({
      finalName: data.name,
      finalImage: data.image,
      instant: isSpecialRollUser() || shouldSkipRollAnimation(),
      showSpecialMessage: isShaduKatUser() && shouldSkipRollAnimation(),
      candidates: rollCandidates
    });

    const message = document.getElementById("message_target");
    const image = document.getElementById("image_target");
    const imageLink = document.getElementById("taskImage");
    imageLink.href = data.link;
    imageLink.setAttribute('data-tip', data.tip);
    message.innerHTML = data.name;
    image.src = resolveTaskImageSource(data.image);
    document.getElementById("start").disabled = true;
    document.getElementById("complete").disabled = false;
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
  req.done(async function(data){
    const rollCandidates = normalizeServerRollCandidates(data.rollCandidates);
    await rollTaskModal({
      finalName: data.name,
      finalImage: data.image,
      instant: isSpecialRollUser() || shouldSkipRollAnimation(),
      showSpecialMessage: isShaduKatUser() && shouldSkipRollAnimation(),
      candidates: rollCandidates.length > 0 ? rollCandidates : getOfficialRollCandidates()
    });

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
    const resolvedImageSource = resolveTaskImageSource(data.image);
    image.src = resolvedImageSource;
    imagePreview.src = resolvedImageSource;
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

function getVerificationItemIds(elementTarget) {
  const hiddenInput = elementTarget.querySelector('.verification-item-ids');
  if (!hiddenInput || !hiddenInput.value) {
    return [];
  }
  return hiddenInput.value
    .split(',')
    .map((value) => parseInt(value.trim(), 10))
    .filter((value) => !Number.isNaN(value));
}

function getCompletedItemIds(elementTarget) {
  const hiddenInput = elementTarget.querySelector('.completed-item-ids');
  if (!hiddenInput || !hiddenInput.value) {
    return [];
  }
  return hiddenInput.value
    .split(',')
    .map((value) => parseInt(value.trim(), 10))
    .filter((value) => !Number.isNaN(value));
}

function getTaskMetaValue(elementTarget, selector) {
  const node = elementTarget.querySelector(selector);
  return node ? node.value : '';
}

function formatUserDateTime(value) {
  if (!value) {
    return '--/--/---- --:--';
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return '--/--/---- --:--';
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(parsedDate);
}

function renderTaskTimestamps() {
  const timestampNodes = document.querySelectorAll('.task-timestamp');
  timestampNodes.forEach((node) => {
    const completedAt = node.getAttribute('data-completed-at');
    node.textContent = formatUserDateTime(completedAt);
  });
}

$(document).ready(function(){
  renderTaskTimestamps();
});

function isoToDateTimeLocal(isoValue) {
  const parsedDate = isoValue ? new Date(isoValue) : new Date();
  const safeDate = Number.isNaN(parsedDate.getTime()) ? new Date() : parsedDate;
  const pad = (value) => String(value).padStart(2, '0');
  const year = safeDate.getFullYear();
  const month = pad(safeDate.getMonth() + 1);
  const day = pad(safeDate.getDate());
  const hours = pad(safeDate.getHours());
  const minutes = pad(safeDate.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function dateTimeLocalToISO(localValue) {
  if (!localValue) {
    return null;
  }
  const parsedDate = new Date(localValue);
  if (Number.isNaN(parsedDate.getTime())) {
    return null;
  }
  return parsedDate.toISOString();
}

function attachFallbackImage(imgElement, fallbackSrc) {
  imgElement.onerror = () => {
    imgElement.onerror = null;
    imgElement.src = fallbackSrc;
  };
}

const verificationItemNameCache = new Map();
const verificationItemNameRequestCache = new Map();
const runeliteItemIdNameCache = new Map();
let runeliteItemIdNameLoadPromise = null;

function toDisplayItemName(itemIdConstantName) {
  return itemIdConstantName
    .toLowerCase()
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ')
    .trim();
}

function loadRuneLiteItemIdNames() {
  if (runeliteItemIdNameLoadPromise) {
    return runeliteItemIdNameLoadPromise;
  }

  const rawItemIdFileUrl = 'https://raw.githubusercontent.com/runelite/runelite/master/runelite-api/src/main/java/net/runelite/api/ItemID.java';
  const itemIdLinePattern = /^\s*public\s+static\s+final\s+int\s+([A-Z0-9_]+)\s*=\s*(\d+)\s*;\s*$/gm;

  runeliteItemIdNameLoadPromise = fetch(rawItemIdFileUrl)
    .then((response) => {
      if (!response.ok) {
        return '';
      }
      return response.text();
    })
    .then((source) => {
      if (!source) {
        return runeliteItemIdNameCache;
      }

      let match = itemIdLinePattern.exec(source);
      while (match !== null) {
        const constantName = match[1];
        const parsedItemId = parseInt(match[2], 10);
        if (!Number.isNaN(parsedItemId) && !runeliteItemIdNameCache.has(parsedItemId)) {
          runeliteItemIdNameCache.set(parsedItemId, toDisplayItemName(constantName));
        }
        match = itemIdLinePattern.exec(source);
      }

      return runeliteItemIdNameCache;
    })
    .catch(() => runeliteItemIdNameCache);

  return runeliteItemIdNameLoadPromise;
}

function formatVerificationItemTooltip(itemId, itemName, isRecorded) {
  const actionHint = isRecorded ? 'click to mark incomplete' : 'click to mark complete';
  const displayName = itemName || 'item';
  return `${displayName}(${itemId}) - ${actionHint}`;
}

function fetchVerificationItemName(itemId) {
  if (verificationItemNameCache.has(itemId)) {
    return Promise.resolve(verificationItemNameCache.get(itemId));
  }

  if (verificationItemNameRequestCache.has(itemId)) {
    return verificationItemNameRequestCache.get(itemId);
  }

  const itemNameRequest = loadRuneLiteItemIdNames()
    .then((itemMap) => {
      const itemName = itemMap.get(itemId) || null;
      verificationItemNameCache.set(itemId, itemName);
      verificationItemNameRequestCache.delete(itemId);
      return itemName;
    })
    .catch(() => {
      verificationItemNameCache.set(itemId, null);
      verificationItemNameRequestCache.delete(itemId);
      return null;
    });

  verificationItemNameRequestCache.set(itemId, itemNameRequest);
  return itemNameRequest;
}

function openTaskActionModal(options) {
  const {
    actionLabel,
    taskName,
    taskTip,
    taskWikiLink,
    itemIds,
    recordedItemIds,
    currentCompletedAtISO,
    allowTimeEdit,
    onConfirm,
  } = options;

  const modal = document.getElementById('taskActionModal');
  const modalTitle = document.getElementById('taskActionModalTitle');
  const modalTip = document.getElementById('taskActionTip');
  const wikiButton = document.getElementById('taskActionWikiButton');
  const progressFill = document.getElementById('taskActionProgressFill');
  const progressText = document.getElementById('taskActionProgressText');
  const itemContainer = document.getElementById('taskActionModalItems');
  const timeInput = document.getElementById('taskActionTimeInput');
  const confirmButton = document.getElementById('taskActionConfirmButton');
  const backButton = document.getElementById('taskActionBackButton');

  if (!modal || !modalTitle || !modalTip || !wikiButton || !progressFill || !progressText || !itemContainer || !timeInput || !confirmButton || !backButton) {
    onConfirm();
    return;
  }

  modalTitle.textContent = taskName || 'Task';
  modalTip.textContent = taskTip || '';
  wikiButton.href = taskWikiLink || '#';
  confirmButton.textContent = actionLabel;

  progressFill.style.width = '100%';
  progressText.textContent = 'Applicable Items';

  timeInput.value = isoToDateTimeLocal(currentCompletedAtISO);
  timeInput.disabled = allowTimeEdit === false;

  itemContainer.innerHTML = '';

  const normalizedItemIds = Array.from(new Set((itemIds || [])
    .map((value) => parseInt(value, 10))
    .filter((value) => !Number.isNaN(value))));
  const selectedItemIds = new Set((recordedItemIds || [])
    .map((value) => parseInt(value, 10))
    .filter((value) => !Number.isNaN(value) && normalizedItemIds.includes(value)));

  const renderItems = () => {
    itemContainer.innerHTML = '';

    if (normalizedItemIds.length === 0) {
      const empty = document.createElement('p');
      empty.className = 'task-action-empty';
      empty.textContent = 'No verification items for this task.';
      itemContainer.appendChild(empty);
      return;
    }

    normalizedItemIds.forEach((itemId) => {
      const isRecorded = selectedItemIds.has(itemId);
      const image = document.createElement('img');
      image.className = `task-action-item ${isRecorded ? 'task-action-item-active' : 'task-action-item-muted'}`;
      attachFallbackImage(image, '/static/clog.png');
      image.src = `https://static.runelite.net/cache/item/icon/${itemId}.png`;
      image.alt = `Item ${itemId}`;
      image.width = 36;
      image.height = 32;
      image.loading = 'lazy';
      image.title = formatVerificationItemTooltip(itemId, null, isRecorded);
      image.setAttribute('role', 'button');
      image.tabIndex = 0;

      fetchVerificationItemName(itemId).then((itemName) => {
        if (!image.isConnected) {
          return;
        }
        image.title = formatVerificationItemTooltip(itemId, itemName, isRecorded);
        image.alt = itemName ? `${itemName} (${itemId})` : `Item ${itemId}`;
      });

      const toggleItem = () => {
        if (selectedItemIds.has(itemId)) {
          selectedItemIds.delete(itemId);
        } else {
          selectedItemIds.add(itemId);
        }
        renderItems();
      };

      image.addEventListener('click', toggleItem);
      image.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggleItem();
        }
      });

      itemContainer.appendChild(image);
    });
  };

  renderItems();

  const closeModal = () => {
    if (typeof modal.close === 'function') {
      modal.close();
    }
  };

  confirmButton.onclick = () => {
    closeModal();
    onConfirm(
      dateTimeLocalToISO(timeInput.value),
      Array.from(selectedItemIds).sort((a, b) => a - b),
    );
  };

  backButton.onclick = () => {
    closeModal();
  };

  if (typeof modal.showModal === 'function') {
    modal.showModal();
  } else {
    onConfirm();
  }
}

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
    const verificationItemIds = getVerificationItemIds(elementTarget);
    const completedItemIds = getCompletedItemIds(elementTarget);
    const taskName = getTaskMetaValue(elementTarget, '.task-name');
    const taskTip = getTaskMetaValue(elementTarget, '.task-tip');
    const taskWikiLink = getTaskMetaValue(elementTarget, '.task-wiki-link');
    const timestampNode = elementTarget.querySelector('.task-timestamp');
    const currentCompletedAtISO = timestampNode ? timestampNode.getAttribute('data-completed-at') : null;

    openTaskActionModal({
      actionLabel: 'Mark Complete',
      taskName: taskName,
      taskTip: taskTip,
      taskWikiLink: taskWikiLink,
      itemIds: verificationItemIds,
      recordedItemIds: completedItemIds,
      currentCompletedAtISO: currentCompletedAtISO,
      allowTimeEdit: true,
      onConfirm: function(selectedCompletedAtISO, selectedItemIds) {
      $('form').submit(false);
      req = $.ajax({
        url :  '/update_completed/',
        type : 'POST',
        data : {
          id : elementTarget.id,
          tier : tier,
          completedAtISO: selectedCompletedAtISO,
          completedItemIds: JSON.stringify(selectedItemIds || []),
        }
      });

      req.done(function(data){
        $(elementTarget).fadeOut(1000).fadeIn(1000);
        $(elementTarget).removeClass('updateButton').addClass('revertButton');
        $(parent).removeClass('incomplete-hover').addClass('complete-hover');
        parent.setAttribute('data-tooltip', 'Mark Incomplete');
        const taskTextNodes = elementTarget.getElementsByTagName('p');
        if (taskTextNodes.length > 1) {
          taskTextNodes[1].textContent = formatUserDateTime(data.completedAtISO);
          taskTextNodes[1].setAttribute('data-completed-at', data.completedAtISO || '');
        }
        const completedIdsNode = elementTarget.querySelector('.completed-item-ids');
        if (completedIdsNode) {
          const returnedIds = Array.isArray(data.completedItemIds) ? data.completedItemIds : [];
          completedIdsNode.value = returnedIds.join(',');
        }
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
    const verificationItemIds = getVerificationItemIds(elementTarget);
    const completedItemIds = getCompletedItemIds(elementTarget);
    const taskName = getTaskMetaValue(elementTarget, '.task-name');
    const taskTip = getTaskMetaValue(elementTarget, '.task-tip');
    const taskWikiLink = getTaskMetaValue(elementTarget, '.task-wiki-link');
    const timestampNode = elementTarget.querySelector('.task-timestamp');
    const currentCompletedAtISO = timestampNode ? timestampNode.getAttribute('data-completed-at') : null;

    openTaskActionModal({
      actionLabel: 'Mark Incomplete',
      taskName: taskName,
      taskTip: taskTip,
      taskWikiLink: taskWikiLink,
      itemIds: verificationItemIds,
      recordedItemIds: completedItemIds,
      currentCompletedAtISO: currentCompletedAtISO,
      allowTimeEdit: false,
      onConfirm: function() {
      $('form').submit(false);
      req = $.ajax({
        url :  '/revert_completed/',
        type : 'POST',
        data : {id : elementTarget.id, tier : tier}
      });

      req.done(function(data){
        $(elementTarget).fadeOut(1000).fadeIn(1000);
        $(elementTarget).removeClass('revertButton').addClass('updateButton');
        $(parent).removeClass('complete-hover').addClass('incomplete-hover');
        parent.setAttribute('data-tooltip', 'Mark Complete');
        const taskTextNodes = elementTarget.getElementsByTagName('p');
        if (taskTextNodes.length > 1) {
          taskTextNodes[1].textContent = '--/--/---- --:--';
          taskTextNodes[1].setAttribute('data-completed-at', '');
        }
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
