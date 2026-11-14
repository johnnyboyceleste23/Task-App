taskList = document.getElementById('task-list');

let draggedItem = null;

taskList.addEventListener('dragstart', function (event) {
    let card = event.target.closest('.task-card[draggable="true"]')
    console.log(card);
    if (!card) {
        return;
    }
    draggedItem = card;
})

taskList.addEventListener('dragover', function (event) {
    event.preventDefault()
    const hoverCard = event.target.closest('.task-card');


    if (!draggedItem || !hoverCard || hoverCard === draggedItem) {
        return;
    }

    const bounds = hoverCard.getBoundingClientRect();
    const middle = bounds.top + bounds.height / 2;

    if (event.clientY < middle) {
        hoverCard.before(draggedItem);
    }
    else {
        hoverCard.after(draggedItem);
    }
})
taskList.addEventListener('drop', function(event) {
    event.preventDefault();
});
taskList.addEventListener("dragend", function () {
    if (!draggedItem) {
        return;
    }

    const cards = taskList.querySelectorAll('.task-card');

    const orderIds = []

    for (const card of cards) {
        orderIds.push(Number(card.dataset.id));

    }
    console.log(orderIds);
    draggedItem = null;

    const csrfToken = document.querySelector(
    'input[name="csrf_token"]'
).value;

fetch('/tasks/reorder', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({ ordered_ids: orderIds })
})
.then(function(response) {
    if (!response.ok) {
        throw new Error('Could not save task order');
    }
    console.log('Order saved');
})
.catch(function(error) {
    console.error(error);
});

})






