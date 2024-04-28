/* global chrome */

import React, { useEffect, useState, useRef } from "react";
import {
  getFromStorage,
  saveToStorage,
  getConfigFromStorage,
  saveConfigToStorage,
} from "../utilities/localStorage";
import LoaderSpinner from "./UI/LoaderSpinner";
import { generateRequestId } from "../utilities/util";

function Welcome({
  videoId,
  infoLoadingError,
  infoLoading,
  isFinancial,
  transcriptSupported,
  getAnalysis,
}) {
  console.log(
    "Welcome rendered:",
    videoId,
    infoLoadingError,
    infoLoading,
    isFinancial,
    transcriptSupported,
    getAnalysis
  );
  return (
    <div className="w-full h-full text-center p-5">
      <img
        src="./skepticklogo.png"
        alt="Skeptick Logo"
        className="w-1/2 mx-auto my-12"
      />
      <div className="mt-24 flex justify-center items-center w-full">
        {!videoId ? (
          <MessageBanner
            message1={"Be vigilant of investment advices"}
            message2={"Visit a youtube video to analyze it"}
          />
        ) : (
          <YoutubeBanner
            videoId={videoId}
            infoLoadingError={infoLoadingError}
            infoLoading={infoLoading}
            isFinancial={isFinancial}
            transcriptSupported={transcriptSupported}
            getAnalysis={getAnalysis}
          />
        )}
      </div>
    </div>
  );
}

function MessageBanner({
  message1,
  message2,
  error = false,
  errorRetry = null,
}) {
  return (
    <div>
      <p className="font-bold mt-8 text-sm">{message1}</p>
      <p
        className={`text-base mt-1 ${error ? "text-red-600" : "text-gray-950"}`}
      >
        {message2}
      </p>
      {error ? (
        <button
          className="text-sm mt-2 text-red-600 rounded-sm"
          onClick={errorRetry}
        >
          ↻ Refresh
        </button>
      ) : (
        ""
      )}
    </div>
  );
}

function YoutubeBanner({
  videoId,
  infoLoadingError,
  infoLoading,
  isFinancial,
  transcriptSupported,
  getAnalysis,
  fetchData,
}) {
  return (
    <div className="w-full">
      {infoLoadingError ? (
        <MessageBanner
          message1={""}
          message2={"Error loading info about the video."}
          error={true}
          errorRetry={fetchData}
        />
      ) : infoLoading ? (
        <LoaderSpinner mode="PRIMARY" size="8" />
      ) : !isFinancial ? (
        <MessageBanner
          message1={"This video is not recognised as a Financial video"}
          message2={"Open a financial video to get its analysis"}
        />
      ) : !transcriptSupported ? (
        <MessageBanner
          message1={"Sorry! English transcript for this video is not available"}
          message2={
            "We're working on multi-language support. Keep looking for the updates."
          }
        />
      ) : (
        <GetAnalysisBanner videoId={videoId} getAnalysis={getAnalysis} />
      )}
    </div>
  );
}

function LoaderElipsis() {
  return (
    <div class="flex space-x-2 justify-center items-center">
      <span class="sr-only">Loading...</span>
      <div class="h-2 w-2 bg-gray-700 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div class="h-2 w-2 bg-gray-700 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div class="h-2 w-2 bg-gray-700 rounded-full animate-bounce"></div>
    </div>
  );
}

function getRiskProfileText(sliderVal) {
  switch (sliderVal) {
    case 1:
      return "Low";
    case 2:
      return "Moderately Low";
    case 3:
      return "Moderate";
    case 4:
      return "Moderately High";
    case 5:
      return "High";
    default:
      return "Moderate";
  }
}

function GetAnalysisBanner({ videoId, getAnalysis }) {
  const [isLoading, setIsLoading] = useState(false);
  const [sliderVal, setSliderVal] = useState(3);
  const [errorOnFetch, setErrorOnFetch] = useState(false);

  const initialFetch = useRef(true);

  useEffect(() => {
    if (initialFetch.current) {
      console.log("use effect slider called", sliderVal);
      getConfigFromStorage("riskProfile", (val) => {
        if (val) {
          setSliderVal(val);
        }
      });
      initialFetch.current = false;
    }
  });

  function handleSliderChange(event) {
    setSliderVal(event.target.value);
  }

  return (
    <div className="w-full px-5">
      <p className="font-semibold text-base mb-3">Choose you risk level 📈</p>
      <div id="slider" className="relative mb-20 w-full">
        <input
          id="steps-range"
          type="range"
          min="1"
          max="5"
          value={sliderVal}
          onChange={handleSliderChange}
          step="1"
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          disabled={isLoading}
        />
        <span className="h-3 w-3 top-1 rounded-full bg-gray-200 absolute start-0 -z-10"></span>
        <span className="h-3 w-3 top-1 rounded-full bg-gray-200 absolute start-1/4 -translate-x-1/4 -z-10"></span>
        <span className="h-3 w-3 top-1 rounded-full bg-gray-200 absolute start-1/2 -translate-x-1/2 -z-10"></span>
        <span className="h-3 w-3 top-1 rounded-full bg-gray-200 absolute end-1/4 translate-x-1/4 -z-10"></span>
        <span className="h-3 w-3 top-1 rounded-full bg-gray-200 absolute end-0 -z-10"></span>

        <span className="text-sm text-gray-700 absolute start-0 -bottom-6 font-semibold">
          Low🦺
        </span>
        <span className="text-sm text-gray-700 absolute start-1/2 -translate-x-1/2 rtl:translate-x-1/2 -bottom-6 font-semibold">
          Moderate💪
        </span>
        <span className="text-sm text-gray-700 absolute end-0 -bottom-6 font-semibold">
          High🔥
        </span>
      </div>

      <button
        className="w-2/3 h-14 text-lg font-bold text-black shadow-lg bg-primary cursor-pointer tracking-wide mx-auto"
        onClick={() =>
          fetchThesis(
            videoId,
            setIsLoading,
            setErrorOnFetch,
            getAnalysis,
            sliderVal
          )
        }
        disabled={isLoading}
      >
        {isLoading ? <LoaderElipsis /> : "Get Skeptick Analysis"}
      </button>

      <p
        className="text-center text-red-600 text-xs"
        style={{ display: !isLoading && errorOnFetch ? "block" : "none" }}
      >
        Error while fetching transcript. Please retry.
      </p>
    </div>
  );
}

function fetchThesis(
  videoId,
  setIsLoading,
  setErrorOnFetch,
  getAnalysis,
  sliderVal
) {
  const riskProfile = getRiskProfileText(sliderVal);
  saveConfigToStorage("riskProfile", sliderVal);
  setIsLoading(true);
  setErrorOnFetch(false);
  getFromStorage(videoId, (result) => {
    if (result && result.thesis.length) {
      console.log("result found", result);
      result.page = "ANALYSIS";
      saveToStorage(videoId, result);
      getAnalysis(result.thesis, result.stockList, riskProfile);
    } else {
      const apiUrl =
        process.env.REACT_APP_API_DOMAIN +
        "/v1/transcribe/breakdown?video_id=" +
        encodeURIComponent(videoId);
      console.log("Calling transcribe...");
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
          if (resp.ok) {
            resp
              .json()
              .then((respObj) => {
                console.log("respObj:transcribe", respObj);
                if (result) {
                  result.thesis = respObj.thesis;
                  result.stockList = respObj.stock_names;
                  result.page = "ANALYSIS";
                  saveToStorage(videoId, result);
                }
                setIsLoading(false);
                getAnalysis(respObj.thesis, respObj.stock_names, riskProfile);
              })
              .catch((err) => {
                setErrorOnFetch(true);
                setIsLoading(false);
              });
          } else {
            setErrorOnFetch(true);
            setIsLoading(false);
          }
        })
        .catch((err) => {
          setErrorOnFetch(true);
          setIsLoading(false);
        });
    }
  });
}

export default Welcome;
