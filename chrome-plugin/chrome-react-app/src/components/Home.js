/* global chrome */

import React, { useEffect, useState, useRef } from "react";
import Welcome from "./Welcome";
import Analysis from "./Analysis";
import { saveToStorage, getFromStorage } from "../utilities/localStorage";
import { generateRequestId } from "../utilities/util";

async function getCurrentTabYoutubeId() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      if (tabs.length > 0) {
        const currentTab = tabs[0];
        const currentTabUrl = currentTab.url;
        console.log("Current tab URL:", currentTabUrl);

        var regExp =
          /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/; // Regular expression to match YouTube video ID
        var match = currentTabUrl.match(regExp);
        resolve(match && match[1] ? match[1] : null);
      } else {
        resolve(null);
      }
    });
  });
}

async function getVideoInfo(youtubeId) {
  console.log("getVideoInfoCalled");
  return new Promise((resolve, reject) => {
    if (!youtubeId) {
      resolve([false, "WELCOME", false, false, [], []]);
    } else {
      getFromStorage(youtubeId, (result) => {
        if (result) {
          resolve([
            false,
            result.page,
            result.isFinancial,
            result.supportedTranscript,
            result.thesis,
            result.stockList,
          ]);
        } else {
          const youtubeUrl = encodeURIComponent(
            "https://www.youtube.com/watch?v=" + youtubeId
          );
          const apiUrl =
            process.env.REACT_APP_API_DOMAIN +
            "/v1/video_id?video_url=" +
            youtubeUrl;
          console.log("Calling video_id...");
          fetch(apiUrl, {
            method: "POST",
            headers: {
              "Content-type": "application/json",
              "x-extension-id": chrome.runtime.id,
              "x-request-id": generateRequestId(),
            },
            body: "",
          })
            .then((resp) => {
              console.log(resp);
              if (resp.ok) {
                resp
                  .json()
                  .then((respObj) => {
                    console.log("getVideoInfo Response", respObj);
                    const store = {
                      page: "WELCOME",
                      isFinancial: respObj.isFinancial
                        ? respObj.isFinancial
                        : false,
                      supportedTranscript: respObj.isEnglish
                        ? respObj.isEnglish
                        : false,
                      thesis: [],
                      stockList: [],
                      updatedAt: Date.now(),
                    };
                    console.log(store);
                    saveToStorage(youtubeId, store);
                    resolve([
                      false,
                      store.page,
                      store.isFinancial,
                      store.supportedTranscript,
                      store.thesis,
                      store.stockList,
                    ]);
                  })
                  .catch(() => {
                    resolve([true, "WELCOME", false, false, [], []]);
                  });
              } else {
                resolve([true, "WELCOME", false, false, [], []]);
              }
            })
            .catch(() => {
              resolve([true, "WELCOME", false, false, [], []]);
            });
        }
      });
    }
  });
}

function Home() {
  const [currPage, setCurrPage] = useState("WELCOME");
  const [youtubeId, setYoutubeId] = useState(null); // null represents that its not youtube page
  const [infoLoading, setInfoLoading] = useState(true);
  const [infoLoadingError, setInfoLoadingError] = useState(false);
  const [isFinancialYoutubeVideo, setIsFinancialYoutubeVideo] = useState(false);
  const [supportedTranscript, setSupportedTranscript] = useState(false);
  const [thesis, setThesis] = useState([]);
  const [stockList, setStockList] = useState([]);
  const [riskProfile, setRiskProfile] = useState("Moderate");

  const initialFetch = useRef(true);

  useEffect(() => {
    if (initialFetch.current) {
      getCurrentTabYoutubeId()
        .then((ytId) => {
          console.log("ytId is", ytId);
          setYoutubeId(ytId);
        })
        .catch(() => {
          setInfoLoadingError(true);
        });
    }
  }, []);

  function fetchData(youtubeId) {
    setInfoLoadingError(false);
    setInfoLoading(true);
    console.log("with youtube id as ", youtubeId);
    getVideoInfo(youtubeId)
      .then((x) => {
        console.log("fetchData: result1: ", x);
        const [
          isError,
          page,
          isFinancial,
          transcriptSupported,
          thesis,
          stockList,
        ] = x;
        console.log(
          "fetchData: result: ",
          isError,
          page,
          isFinancial,
          transcriptSupported,
          thesis,
          stockList
        );
        setInfoLoadingError(isError);
        setCurrPage(page);
        setInfoLoading(false);
        setIsFinancialYoutubeVideo(isFinancial);
        setSupportedTranscript(transcriptSupported);
        setThesis(thesis);
        setStockList(stockList);
      })
      .catch(() => {
        setInfoLoadingError(true);
        setCurrPage("WELCOME");
        setInfoLoading(false);
        setIsFinancialYoutubeVideo(false);
        setSupportedTranscript(false);
        setThesis([]);
        setStockList([]);
      });
  }

  useEffect(() => {
    fetchData(youtubeId);
  }, [youtubeId]);

  const getAnalysis = (thesisList, stockList, riskProfile) => {
    setThesis(thesisList);
    setStockList(stockList);
    setRiskProfile(riskProfile);
    setCurrPage("ANALYSIS");
  };

  const goBack = (videoId) => {
    // TODO: set page as
    getFromStorage(videoId, (result) => {
      result.page = "WELCOME";
      saveToStorage(videoId, result);
    });
    setCurrPage("WELCOME");
  };

  return (
    <div className="m-0 p-0" id="popup-body">
      {currPage === "WELCOME" ? (
        <Welcome
          videoId={youtubeId}
          infoLoadingError={infoLoadingError}
          infoLoading={infoLoading}
          isFinancial={isFinancialYoutubeVideo}
          transcriptSupported={supportedTranscript}
          getAnalysis={getAnalysis}
          fetchData={() => {
            fetchData(youtubeId);
          }}
        />
      ) : (
        <Analysis
          goBack={() => goBack(youtubeId)}
          videoId={youtubeId}
          thesis={thesis}
          stockList={stockList}
          riskProfile={riskProfile}
        />
      )}
    </div>
  );
}

export default Home;
