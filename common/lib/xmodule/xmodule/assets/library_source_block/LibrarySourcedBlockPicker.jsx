/* globals gettext */

import 'whatwg-fetch';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'underscore';

class LibrarySourcedBlockPicker extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      libraries: [],
      xblocks: [],
      searchedLibrary: '',
      searchedXblock: '',
      selectedLibrary: undefined,
      selectedXblocks: new Set(this.props.selectedXblocks),
    };
    this.onLibrarySelected = this.onLibrarySelected.bind(this);
    this.onXblockSelected = this.onXblockSelected.bind(this);
    this.onLibraryInputChange = this.onLibraryInputChange.bind(this);
    this.onXBlockInputChange = this.onXBlockInputChange.bind(this);
    this.onSaveClick = this.onSaveClick.bind(this);
    this.onDeleteClick = this.onDeleteClick.bind(this);
    this.fetchLibraries();
  }

  onLibraryInputChange(event) {
    /* signal to React not to nullify the event object */
    event.persist();
    this.setState({
      searchedLibrary: event.target.value
    })

    if (!this.debouncedFetchLibraries) {
      this.debouncedFetchLibraries =  _.debounce(() => {
         let searchString = event.target.value;
         this.fetchLibraries(event.target.value);
      }, 300);
    }
    this.debouncedFetchLibraries();
  }

  onXBlockInputChange(event) {
    /* signal to React not to nullify the event object */
    event.persist();
    this.setState({
      searchedXblock: event.target.value
    })

    if (!this.debouncedFetchXblocks) {
      this.debouncedFetchXblocks =  _.debounce(() => {
         let searchString = event.target.value;
         this.fetchXblocks(this.state.selectedLibrary, event.target.value);
      }, 300);
    }
    this.debouncedFetchXblocks();
  }

  fetchLibraries(text_search='') {
    fetch(`/api/libraries/v2?text_search=${text_search}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(res => res.json())
    .then((response) => {
      this.setState({
        libraries: response,
      })
    });
  }

  fetchXblocks(library, text_search='') {
    fetch(`/api/libraries/v2/${library}/blocks?text_search=${text_search}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(res => res.json())
    .then((response) => {
      this.setState({
        xblocks: response
      })
    });
  }

  onLibrarySelected(event) {
    this.setState({
      selectedLibrary: event.target.value,
    })
    this.fetchXblocks(event.target.value)
  }

  onXblockSelected(event) {
    let state = new Set(this.state.selectedXblocks)
    if (event.target.checked) {
      state.add(event.target.value)
    } else {
      state.delete(event.target.value)
    }
    this.setState({
      selectedXblocks: state
    })

  }

  onSaveClick() {
    console.log(this.state.selectedXblocks)
    $('#library-sourced-block-picker').trigger('save', {
      save_url: this.props.saveUrl,
      source_block_ids: Array.from(this.state.selectedXblocks),
    })
  }

  onDeleteClick(event) {
    let state = new Set(this.state.selectedXblocks)
    state.delete(event.target.dataset.value)
    this.setState({
      selectedXblocks: state
    })
  }

  render() {
    return (
      <section>
        <div style={{display: "flex", flexDirection: "row"}}>
          <div style={{display: "flex", flexDirection: "column", border: "1px solid #ccc", margin: "10px"}}>
            <input placeholder="Search for libary" value={this.state.searchedLibrary} onChange={this.onLibraryInputChange}/>
            <div className="list-group" style={{padding:"5px"}} onChange={this.onLibrarySelected} value={this.state.selectedLibrary}>
              {
              this.state.libraries.map(lib => (
                <div key={lib.id}>
                  <input id={`sourced-library-${lib.id}`} type="radio" value={lib.id} name="library"/>
                  <label htmlFor={`sourced-library-${lib.id}`}>{lib.title}</label>
                </div>
              ))
            }
            </div>
          </div>
          <div style={{display: "flex", flexDirection: "column", border: "1px solid #ccc", margin: "10px"}}>
            <input placeholder="Search for XBlocks" onChange={this.onXBlockInputChange}/>
            <div className="list-group" style={{padding:"5px"}} onChange={this.onXblockSelected}>
              {
              this.state.xblocks.map(block => (
                <div key={block.id}>
                  <input id={`sourced-block-${block.id}`} type="checkbox" value={block.id} name="block" checked={this.state.selectedXblocks.has(block.id)} readOnly/>
                  <label htmlFor={`sourced-block-${block.id}`}>{block.display_name} ({block.id})</label>
                </div>
              ))
            }
            </div>
          </div>
          <div style={{display: "flex", flexDirection: "column", border: "1px solid #ccc", margin: "10px"}}>
            <h4> Selected blocks </h4>
            <ul>
              {
                Array.from(this.state.selectedXblocks).map(block => (
                  <li key={block} style={{display: "flex", flexDirection: "row", justifyContent: "space-between"}}>
                    <label>
                      {block}
                    </label>
                    <button data-value={block} onClick={this.onDeleteClick}>x</button>
                  </li>
                ))
              }
            </ul>
          </div>
        </div>
        <button className="btn-brand save-btn" onClick={this.onSaveClick}>Save</button>
      </section>
    );
  }
}

LibrarySourcedBlockPicker.propTypes = {
  saveUrl: PropTypes.string,
  selectedXblocks: PropTypes.array,
};

LibrarySourcedBlockPicker.defaultProps = {
  saveUrl: '',
  selectedXblocks: [],
};

export { LibrarySourcedBlockPicker }; // eslint-disable-line import/prefer-default-export
