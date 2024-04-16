/* global chrome */

function saveToStorage(key, value, callback) {
  const maxKeys = process.env.REACT_APP_STORAGE_LIMIT;
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
        if (Object.keys(items).length >= maxKeys) {
          let keysToDelete = Object.keys(items)
            .sort((a, b) => items[a].updatedAt - items[b].updatedAt)
            .slice(0, Object.keys(items).length - maxKeys + 1);
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

function getFromStorage(key, callback) {
  chrome.storage.local.get(key, function (result) {
    if (result[key]) {
      saveToStorage(key, result[key]);
    }
    callback(result[key]);
  });
}

module.exports = {
	saveToStorage, 
	getFromStorage
}
