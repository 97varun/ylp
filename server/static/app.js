input = document.getElementById('search-bar');
searchButton = document.getElementById('search-button');

outputTitle = document.getElementById('card-title');
outputContent = document.getElementById('card-content');

const baseUrl = 'http://localhost:8080';

var xhrObj = {
    xhr: new XMLHttpRequest(),

    createPlaylist: function (query) {
        this.xhr.onreadystatechange = this.update;
        this.xhr.open("POST", `${baseUrl}/youtubelearningplaylist`, true);

        console.log(`query ${query}`);

        outputContent.innerHTML = 'Loading...'

        this.xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        this.xhr.send(`query=${encodeURIComponent(query)}`);
    },

    update: function () {
        if (this.readyState == 4 && this.status == 201) {
            var result = JSON.parse(this.responseText);
            console.log(`Playlist: ${result['playlistUrl']}`);

            outputTitle.innerHTML = `Learning playlist(s)`;

            var playlistUrlAchors = result['playlistUrl'].map((playlistUrl) => {
                return `<a target="_blank" href="${playlistUrl}">${playlistUrl}</a>`
            });

            outputContent.innerHTML = `${playlistUrlAchors.join(', ')}`;
        }
        else if (this.readyState == 4 && this.status >= 400) {
            var result = JSON.parse(this.responseText);
            console.log(`Error: ${result['error']}`);

            outputContent.innerHTML = `Error: ${result['error']}`;
        }
    }
}

function search(e) {
    if (e.keyCode == 13 || (e.type == 'click' && e.currentTarget.id == 'search-button')) {
        var query = input.value;
        xhrObj.createPlaylist(query);
    }
}

input.onkeypress = search;
searchButton.onclick = search;