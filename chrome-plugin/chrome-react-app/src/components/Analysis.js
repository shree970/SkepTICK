/* global chrome */
import React, { useEffect, useState, useRef } from "react";
import LoaderSpinner from "./UI/LoaderSpinner";
import { generateRequestId } from "../utilities/util";

function Navbar({ selectedTab, setSelectedTag, goBack }) {
  const tabs = [
    { key: "WHOLETRUTH", label: "Wholetruth" },
    { key: "STOCK_SUMMARY", label: "Stock Summary" },
    { key: "BACKTEST", label: "Backtest" },
  ];
  return (
    <div className="bg-primary p-3 flex flex-wrap items-center">
      <button
        type="button"
        class="flex-shrink-0 flex items-center justify-center text-gray-700"
        onClick={goBack}
      >
        <svg
          class="w-5 h-5 rtl:rotate-180"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6.75 15.75L3 12m0 0l3.75-3.75M3 12h18"
          />
        </svg>
      </button>

      <div className="ml-auto mr-2">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`ml-4 rounded-xl border-0 px-2 py-1 text-gray-900 ${
              selectedTab === tab.key
                ? "bg-white font-bold"
                : "bg-gray-200 font-medium"
            }`}
            onClick={() => setSelectedTag(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function Wholetruth({
  thesisMappedList,
  isLoading,
  errorOnFetch,
  fetchWholetruth,
}) {
  return (
    <div className="p-6 pt-8">
      <p className="text-sm text-black text-center mb-5 italic">
        <b>'Thesis'</b> Presented in the Video
      </p>
      <ul>
        {thesisMappedList.map(({ thesis, wholetruth }, i) => (
          <li className="mb-8">
            <p className="font-semibold text-justify text-sm px-4">
              <span className="text-xl leading-none">{i + 1}</span> &nbsp; {thesis}
            </p>
            <div className="bg-primaryt space-x-4 flex items-center rounded-b p-4">
              <span className="flex-shrink-0 rounded-full bg-gray-100 w-5 h-5 flex items-center justify-center">
                ❗
              </span>
              <p className="text-justify text-xs ml-auto font-semibold">
                {isLoading ? (
                  <i className="text-gray-800 italic">
                    Finding '<b>WholeTruth</b>' behind this ...
                  </i>
                ) : errorOnFetch ? (
                  <i
                    className="text-red-600 italic cursor-pointer"
                    onClick={fetchWholetruth}
                  >
                    Error while fetching, Click here to retry ⟳
                  </i>
                ) : (
                  wholetruth
                )}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Backtest() {
  return (
    <div className="p-6 pt-8">
      <p className="text-lg text-black text-center font-semibold my-8">
        How Does Your Stock Stack Up Against Youtube's Hype ?
      </p>
      <p className="text-base mb-1 mt-24 text-center text-gray-900 italic">
        Backtest these claims against a stock's historical data
      </p>
      <p className="text-center text-base font-bold">Coming Soon</p>
    </div>
  );
}

function StockSummary({
  stockList,
  selectedStock,
  setSelectedStock,
  stockSummary,
  setStockSummary,
  sourceList,
  setSourceList,
  isLoading,
  errorOnFetch,
  setIsLoading,
  setErrorOnFetch,
}) {
  const handleSelectChange = (e) => {
    setSelectedStock(e.target.value);
  };

  const handleSummarize = () => {
    console.log("fetching stock for: ", selectedStock);
    setIsLoading(true);
    setErrorOnFetch(false);
    const apiUrl =
      process.env.REACT_APP_API_DOMAIN +
      "/v1/stock_summary/" +
      encodeURIComponent(selectedStock);
    console.log("Calling stock summary ...");
    fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-type": "application/json",
        "x-extension-id": chrome.runtime.id,
        "x-request-id": generateRequestId(),
      },
      body: JSON.stringify({
        stock_name: selectedStock,
      }),
    })
      .then((resp) => {
        if (resp.ok) {
          resp
            .json()
            .then((respObj) => {
              console.log("respObj:handleSummarize", respObj);
              setStockSummary(respObj.stock_summary);
              const sources = respObj.sources.map((s) => {
                return { message: s.Headline, source: s.Link };
              });
              setSourceList(sources);
              setIsLoading(false);
            })
            .catch(() => {
              setIsLoading(false);
              setErrorOnFetch(true);
            });
        } else {
          setIsLoading(false);
          setErrorOnFetch(true);
        }
      })
      .catch(() => {
        setIsLoading(false);
        setErrorOnFetch(true);
      });
  };

  return (
    <div className="p-6 pt-8">
      <p className="text-xs text-black text-center mb-5 italic font-semibold">
        Know What's Latest on the Stocks mentioned with our Summarizer
      </p>
      {!stockList.length ? (
        <p className="text-base text-center leading-relaxed font-semibold">
          No stocks are mentioned in the Video
        </p>
      ) : (
        <div className="mt-8">
          <div className="mx-auto w-2/3 flex items-center">
            <select
              value={selectedStock}
              onChange={handleSelectChange}
              className="mr-2 p-2 border flex-grow "
            >
              {stockList.map((option, index) => (
                <option key={index} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <button
              onClick={handleSummarize}
              className="p-2 bg-blue-500 text-white "
              disabled={isLoading}
            >
              Summarize
            </button>
          </div>

          <div className="flex justify-center items-center mt-2">
            {isLoading ? (
              <LoaderSpinner mode={"PRIMARY"} />
            ) : errorOnFetch ? (
              <p className="text-red-600 italic text-xs text-center">
                Error while fetching summary. Please retry
              </p>
            ) : (
              ""
            )}
          </div>

          <div style={{ display: stockSummary ? "block" : "none" }}>
            <p className="mt-6 px-6 font-bold">Summary:</p>
            <div className="mt-4 px-8 font-semibold text-justify">
              &emsp;{stockSummary}
            </div>
            <p className="mt-8 px-6 font-bold">Sources:</p>
            <ol className="mt-4 px-8 font-semibold">
              {sourceList.map((sourceObj) => (
                <li className="my-2">
                  {sourceObj.message} &nbsp; [
                  <a
                    href={sourceObj.source}
                    className="text-blue-600 underline"
                  >
                    {sourceObj.source}
                  </a>
                  ]
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

function Analysis({ goBack, videoId, thesis, stockList, riskProfile }) {
  const [selectedTab, setSelectedTag] = useState("WHOLETRUTH"); // 'WHOLETRUTH' | 'BACKTEST' | 'STOCK_SUMMARY'
  const [selectedStock, setSelectedStock] = useState(stockList[0]);
  const [stockSummary, setStockSummary] = useState("");
  const [sourceList, setSourceList] = useState([]);
  const [thesisMappedList, setThesisMappedList] = useState(
    thesis.map((t) => {
      return { thesis: t, wholetruth: "" };
    })
  );
  const [isLoadingWholeTruth, setIsLoadingWholeTruth] = useState(true);
  const [errorOnFetchWholeTruth, setErrorOnFetchWholeTruth] = useState(false);
  const [isLoadingStockSummary, setIsLoadingStockSummary] = useState(false);
  const [errorOnFetchStockSummary, setErrorOnFetchStockSummary] =
    useState(false);

  function fetchWholetruth() {
    setIsLoadingWholeTruth(true);
    setErrorOnFetchWholeTruth(false);
    const apiUrl =
      process.env.REACT_APP_API_DOMAIN +
      "/v1/whole_truth?video_id=" +
      encodeURIComponent(videoId) +
      "&risk_profile=" +
      encodeURIComponent(riskProfile);
    console.log("Calling whole truth ..");
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
              console.log("respObj:whole_truth", respObj);
              const wholetruths = respObj.whole_truth;
              const mappedList = thesisMappedList.map((t, i) => {
                t.wholetruth = wholetruths[i];
                return t;
              });
              setThesisMappedList(mappedList);
              console.log("thesisMappedList new: ", mappedList);
              setIsLoadingWholeTruth(false);
            })
            .catch(() => {
              setErrorOnFetchWholeTruth(true);
              setIsLoadingWholeTruth(false);
            });
        } else {
          setErrorOnFetchWholeTruth(true);
          setIsLoadingWholeTruth(false);
        }
      })
      .catch(() => {
        setErrorOnFetchWholeTruth(true);
        setIsLoadingWholeTruth(false);
      });
  }

  const initialFetch = useRef(true);

  useEffect(() => {
    if (initialFetch.current) {
      fetchWholetruth(); // Call without parameters if they are not needed
      initialFetch.current = false;
    }
  });

  return (
    <div className="h-full">
      <Navbar
        selectedTab={selectedTab}
        setSelectedTag={setSelectedTag}
        goBack={goBack}
      />
      <div className="bg-white w-full overflow-y-auto">
        {selectedTab === "WHOLETRUTH" ? (
          <Wholetruth
            thesisMappedList={thesisMappedList}
            isLoading={isLoadingWholeTruth}
            errorOnFetch={errorOnFetchWholeTruth}
            fetchWholetruth={fetchWholetruth}
          />
        ) : selectedTab === "BACKTEST" ? (
          <Backtest />
        ) : (
          <StockSummary
            stockList={stockList}
            selectedStock={selectedStock}
            setSelectedStock={setSelectedStock}
            stockSummary={stockSummary}
            setStockSummary={setStockSummary}
            sourceList={sourceList}
            setSourceList={setSourceList}
            isLoading={isLoadingStockSummary}
            setIsLoading={setIsLoadingStockSummary}
            errorOnFetch={errorOnFetchStockSummary}
            setErrorOnFetch={setErrorOnFetchStockSummary}
          />
        )}
      </div>
    </div>
  );
}

export default Analysis;
