import React, { Component } from 'react';
import NewWindow from 'react-new-window'
import { ReactiveBase,
        DataSearch,
        DateRange,
        StateProvider,
        ReactiveList,
        ResultList,
        SelectedFilters,
        MultiList
} from '@appbaseio/reactivesearch';
import "./App.css";
import ExpandDiv from './ExpandDiv'
import PdfViewer from './PdfViewer'

const { ResultListWrapper } = ReactiveList;

function serverQuery(value) {
  console.log('Call serverQuery')
  console.log(value)

  fetch("http://localhost/api/common/build_query",{
    method: "POST",
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      index_name: 'iga',
      value: value
    })
  }).then(function(response) {
      if(response.ok) {
        response.json().then(function(data) {
          return {query: data[0].query}
          });
      } else {
        console.log('Mauvaise réponse du réseau');
        console.log(response);

      }
    })
    .catch(function(error) {
    console.log('Il y a eu un problème avec l\'opération fetch: ' + error.message);
  });
}

class App extends React.Component {
  constructor(props) {
  super(props);
  this.state = { dsl: '' };
  }

  render() {
    return (

      <div className="main-container">


        <ReactiveBase
          app="iga"
          url="http://localhost/elasticsearch"
        >

        <DataSearch
        componentId="SearchFilter"
        dataField={["content","title"]}
        className="search-bar"
        queryFormat="or"
        placeholder="Search for documents..."
        innerClass={{
            title: 'search-title',
            input: 'search-input'
        }}
        highlight={true}
        autosuggest={false}//no dropdown suggestion
        customHighlight={props => ({
      		highlight: {
            pre_tags: ['<mark>'],
            post_tags: ['</mark>'],
      			fields: {
      				content:{},
      				title: {},
      			},
            "fragment_size" : 300,
            "number_of_fragments" : 3,
            "order" : "score",
            "boundary_scanner" : "sentence",
            "boundary_scanner_locale" : "fr-FR"
      		},
      	})}

      />

        {
          <DataSearch
          componentId="SearchFilterServer"
          placeholder="Custom search for documents on server..."
          customQuery={
              function(value, props) {
                if (value==undefined || 0 === value.length){
                  console.log('no value')
                } else {
                  const query = serverQuery(value)
                  console.log('Response is')
                  console.log(query)
                  return query

              }
            }
          }
          />
        }



        <StateProvider
        includeKeys={['query']}
        render={({ searchState }) => {
            this.setState({dsl : JSON.stringify(searchState.SearchResult, undefined, 2)})
            return null
        }}
        />

        <DateRange
          componentId="DateFilter"
          dataField="date"
        />


        <SelectedFilters
            showClearAll={true}
            clearAllLabel="Clear filters"
        />



        <ExpandDiv value={this.state.dsl}/>



        <ReactiveList
            react={{ //https://docs.appbase.io/docs/reactivesearch/v3/advanced/reactprop/
              "and" : {
                "or": ["SearchFilterServer", "SearchFilter"],
                "and":["DateFilter"]
              }
            }}
            componentId="SearchResult"
        >
          {({ data }) => (
              <ResultListWrapper>
                  {
                      data.map(item => {
                          // handle
                          let href=decodeURI(item._id).replace(/\+/g, " ")

                          return (
                          //href = decodeURI(item._id)
                          //console.log(decodeURI(item._id))

                          <ResultList key={item._id} href={`/pdfjs-2.3.200-dist/web/viewer.html?file=/user/pdf/${href}`}>
                              <ResultList.Content>
                                  <ResultList.Title
                                      dangerouslySetInnerHTML={{
                                          __html: item.title
                                      }}
                                  />
                                  <ResultList.Description
                                        dangerouslySetInnerHTML={{
                                          __html: item.content
                                      }}
                                  />
                                  <div>
                                  <div>Par {item.author}</div>
                                  <span>
                                      Pub {item.date}
                                  </span>
                                  </div>
                              </ResultList.Content>
                          </ResultList>
                      )})
                  }
              </ResultListWrapper>
          )}
        </ReactiveList>

        </ReactiveBase>
      </div>
    );
  }
}

export default App;
