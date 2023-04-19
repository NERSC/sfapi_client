const ASYNCHRONOUS = "Asynchronous";
const SYNCHRONOUS = "Synchronous";
const ASYNC_PREFIX = "/async";
const SYNC_PREFIX = "/sync";
const SFAPI_CLIENT = "sfapi_client";
const SFAPI_CLIENT_SYNC = "Sync";
const SFAPI_CLIENT_ASYNC = "Async";
const MD_NAV_LINK = "md-nav__link";
const MD_HEADER_TOPIC = "md-header__topic";
// Note: We are reuse styling from the version selector.
// We should probably generate our CSS in the future.
const MD_APISELECTOR_LINK = "md-version__link";
const MD_APISELECTOR_ITEM = "md-version__item";
const MD_APISELECTOR = "md-version";
const MD_APISELECTOR_CURRENT = "md-version__current";
const MD_APISELECTOR_LIST = "md-version__list";

const findNavAnchor = (textContent) => {
  for (const e of Array.from(
    document.getElementsByClassName(MD_NAV_LINK)
  ).filter((e) => e.tagName.toLowerCase() === "label")) {
    if (e.textContent.trim() === textContent) {
      return e;
    }
  }

  return undefined;
};

let buttonLabel;

const renderListItem = (label) => {
  const item = document.createElement("li");
  const link = document.createElement("a");
  link.setAttribute("class", MD_APISELECTOR_LINK);
  link.setAttribute("onclick", "onClick(event)");
  link.appendChild(document.createTextNode(label));
  item.setAttribute("class", MD_APISELECTOR_ITEM);
  item.appendChild(link);

  return item;
};

const renderAsyncSyncSelector = () => {
  const topic = document.getElementsByClassName(MD_HEADER_TOPIC);
  const div = document.createElement("div");
  div.setAttribute("class", MD_APISELECTOR);
  const button = document.createElement("button");
  button.setAttribute("class", MD_APISELECTOR_CURRENT);
  const ul = document.createElement("ul");
  ul.setAttribute("class", MD_APISELECTOR_LIST);

  const sync = renderListItem(ASYNCHRONOUS);
  const async = renderListItem(SYNCHRONOUS);
  ul.appendChild(sync);
  ul.appendChild(async);

  buttonLabel = document.createTextNode(SYNCHRONOUS);
  button.appendChild(buttonLabel);
  div.appendChild(button);
  div.appendChild(ul);
  topic[0].appendChild(div);
};

const enableElement = (id) => {
  const async = document.getElementById(SFAPI_CLIENT_ASYNC);
  const sync = document.getElementById(SFAPI_CLIENT_SYNC);

  if (id == SFAPI_CLIENT_ASYNC) {
    async.style.display = "list-item";
    sync.style.display = "none";
    buttonLabel.textContent = ASYNCHRONOUS;
  } else {
    async.style.display = "none";
    sync.style.display = " list-item";
    buttonLabel.textContent = SYNCHRONOUS;
  }
};

const updateURL = (prefix) => {
  if (location.pathname === "/") {
    location.pathname = `/reference${prefix}/client`;
  } else if (prefix === SYNC_PREFIX && !location.pathname.includes(prefix)) {
    location.pathname = location.pathname.replace(ASYNC_PREFIX, prefix);
  } else if (!location.pathname.includes(prefix)) {
    location.pathname = location.pathname.replace(SYNC_PREFIX, prefix);
  }
};

const showSync = () => {
  enableElement(SFAPI_CLIENT_SYNC);
  updateURL(SYNC_PREFIX);
};

const showAsync = () => {
  enableElement(SFAPI_CLIENT_ASYNC);
  updateURL(ASYNC_PREFIX);
};

const initNavMenu = () => {
  [SFAPI_CLIENT_SYNC, SFAPI_CLIENT_ASYNC].forEach((textContent) => {
    const a = findNavAnchor(textContent);
    // Rename the text
    a.textContent = SFAPI_CLIENT;

    // Tag the li associated with the anchor so we can find it
    const li = a.parentElement;
    li.setAttribute("id", textContent);
  });

  if (location.pathname === "/") {
    showSync();
  } else if (location.pathname.includes(SYNC_PREFIX)) {
    showSync();
  } else if (location.pathname.includes(ASYNC_PREFIX)) {
    showAsync();
  }
};

const onClick = (e) => {
  if (e.target.textContent == ASYNCHRONOUS) {
    showAsync();
  } else {
    showSync();
  }
};

const init = () => {
  renderAsyncSyncSelector();
  initNavMenu();
};

init();
