let btnDownload = document.getElementById("btnDownload");
let chkAudio = document.getElementById("chkAudio");
let chkVideo = document.getElementById("chkVideo");
let chkSub = document.getElementById("chkSub");

let SERVERIP = "http://192.168.1.121:8908"

// When the button is clicked, inject make a new TAB, this is basically a GET
// call that bypasses CORS
btnDownload.addEventListener("click", async () => {
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const active_url_data = new URL(tab.url);
    if (active_url_data.origin.indexOf("youtube.com") >= 0) {
        let video_id = active_url_data.searchParams.get("v");        
        if (video_id !== null)
        {
            let qrurl = SERVERIP + "/download?v=" + video_id;
            if (chkSub.checked) {
                qrurl = qrurl + "&" + "s=1";
            } else {
                qrurl = qrurl + "&" + "s=0";
            }
            if (chkAudio.checked) {
                qrurl = qrurl + "&" + "a=1";
            } else {
                qrurl = qrurl + "&" + "a=0";
            }
            if (chkVideo.checked) {
                qrurl = qrurl + "&" + "d=1";
            } else {
                qrurl = qrurl + "&" + "d=0";
            }
            let created = await chrome.tabs.create({active: false, url: qrurl});
        }
    }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Close the tabs we open after they load
    if (tab.url.indexOf(SERVERIP) != -1 && changeInfo.status == 'complete') {
        chrome.tabs.remove(tabId);
    }
});