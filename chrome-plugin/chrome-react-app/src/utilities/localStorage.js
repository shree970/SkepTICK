/* global chrome */

const prefix = 'yId-'; 

function saveToStorage(youtubeId, value, callback) {
  const key = prefix + youtubeId;
  const maxKeys = Number(process.env.REACT_APP_STORAGE_LIMIT);
  value.updatedAt = Date.now();

  chrome.storage.local.get(key, (result) => {
    if (result) {
      const newValue = {};
      newValue[key] = value;
      chrome.storage.local.set(newValue, () => {
        callback();
      });
    } else {
      chrome.storage.local.get(null, (items) => {
        const filteredKeys = Object.keys(items).filter(key => key.startsWith(prefix));;
        if (filteredKeys.length >= maxKeys) {
          let keysToDelete = filteredKeys
            .sort((a, b) => items[a].updatedAt - items[b].updatedAt)
            .slice(0, filteredKeys.length - maxKeys + 1);
          chrome.storage.local.remove(keysToDelete, function () {
            let newValue = {};
            newValue[key] = value;
            chrome.storage.local.set(newValue, () => {
              callback();
            });
          });
        } else {
          let newValue = {};
          newValue[key] = value;
          chrome.storage.local.set(newValue, () => {
            callback();
          });
        }
      });
    }
  });
}

function getFromStorage(youtubeId, callback) {
  const key = prefix + youtubeId
  chrome.storage.local.get(key, (result) => {
    if (result[key]) {
      saveToStorage(youtubeId, result[key]);
    }
    callback(result[key]);
  });
}

module.exports = {
  saveToStorage,
  getFromStorage,
};
