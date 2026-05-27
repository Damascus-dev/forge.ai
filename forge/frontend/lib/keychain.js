let _apiKey = "";

export function getApiKey() {
  return _apiKey;
}

export function setApiKey(key) {
  _apiKey = key;
}

export function clearApiKey() {
  _apiKey = "";
}
