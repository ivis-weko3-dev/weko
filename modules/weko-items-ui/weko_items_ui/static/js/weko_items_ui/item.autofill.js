class ModalHeader extends React.Component {
    render() {
        return (
            <div className="text-left">
                <h3>{this.props.headerName}</h3>
            </div>
        )
    }
}
class SearchMetaForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            idType: '',
            itemId: '',
            selectOptions: []
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    componentDidMount() {
        axios.get('/api/autofill/select_options')
            .then(res => res.data)
            .then((result) => {
                let options = result.options.map((option) => {
                    return (
                        <option key={option.value} value={option.value}>{option.text}</option>
                    )
                });
                this.setState({
                    selectOptions: options
                });
            }
            )
            .catch((error) => {
                alert(error);
            });
    }

    handleChange(event) {
        const target = event.target;
        const value = target.value;
        const name = target.name;
        this.setState({ [name]: value });
    }

    handleSubmit(event) {
        this.clickItemMetadata();
        event.preventDefault();
    }

    clickItemMetadata() {
        setTimeout(function () {
            angular.element('#btn_setItemMetadata').triggerHandler('click');
        }, 0);
    };

    render() {

        if (this.state.idType === 'researchmap') {
            return (
                <div>
                <ModalHeader headerName={this.props.headerName} />
                <br></br>
                <form onSubmit={this.handleSubmit}>
                    <div className="form-inline">
                        <label className="input-group-text" for="autofill_id_type">
                            {this.props.selectMeta}
                        </label>
                        &nbsp;&nbsp;
                        <select name="idType" id="autofill_id_type" value={this.state.idType.value}
                            onChange={this.handleChange} className="form-control">
                            {this.state.selectOptions}
                        </select>
                        &nbsp;&nbsp;
                        <div className="form-horizontal">
                            <div className="col-md-12 form-group">
                                <div className="col-md-4">
                                    <label className="control-label" for="parmalink">
                                        {this.props.autofill_parmalink}
                                    </label>
                                </div>
                                <div className="col-md-8">
                                    <input name="parmalink" type="text" id="parmalink"
                                        value={this.state.parmalink} onChange={this.handleChange}
                                        className="form-control ng-untouched ng-pristine ng-valid" />
                                </div>
                            </div>
                            <div className="col-md-12 form-group">
                                <div className="col-md-4">
                                    <label className="control-label" for="achievement_type">
                                        {this.props.achievement_type}
                                    </label>
                                </div>
                                <div className="col-md-8">
                                    <select name="achievement_type" id="achievement_type" value={this.state.achievement_type}
                                        onChange={this.handleChange} className="form-control">
                                        <option key="published_papers" value="published_papers">{this.props.autofill_published_papers}</option>
                                        <option key="misc" value="misc">{this.props.autofill_misc}</option>
                                        <option key="books_etc" value="books_etc">{this.props.autofill_books_etc}</option>
                                        <option key="presentations" value="presentations">{this.props.autofill_presentations}</option>
                                        <option key="works" value="works">{this.props.autofill_works}</option>
                                        <option key="others" value="others">{this.props.autofill_others}</option>
                                    </select>
                                    &nbsp;&nbsp;
                                </div>
                            </div>
                            <div className="col-md-12 form-group">
                                <div className="col-md-4">
                                    <label className="control-label" for="achievement_id">
                                        {this.props.achievement_id}
                                    </label>
                                </div>
                                <div className="col-md-8">
                                    <input type="text" id="achievement_id" className="form-control ng-untouched ng-pristine ng-valid" />
                                </div>
                            </div>
                            <div className="col-md-12 form-group">
                                <div className="col-md-4">
                                    <label className="control-label" for="enable_item_achievement_link">
                                        {this.props.enable_item_achievement_link}
                                    </label>
                                </div>
                                <div className="col-md-8">
                                    {this.props.cris_linkage_linked_ids.length > 0 ? (
                                        <React.Fragment>
                                            <input type="checkbox" id="enable_item_achievement_link" className="checkbox form-control ng-untouched ng-pristine ng-valid" disabled />
                                            <span style={{color: "red", marginLeft: "10px"}}>{this.props.cris_linkage_linked_message}</span>
                                        </React.Fragment>
                                    ) : (
                                        <input type="checkbox" id="enable_item_achievement_link" className="checkbox form-control ng-untouched ng-pristine ng-valid" />
                                    )}
                                </div>
                            </div>
                        </div>
                        <p className="text-center">
                            <input type="submit" id="autofill_item_button" value={this.props.getValue} className="btn btn-info" />
                        </p>
                    </div>
                    <br />
                    <div id="auto-fill-error-div">
                        <span id="autofill-error-message"></span>
                    </div>
                </form>
            </div>
            )
        }



        return (
            <div>
                <ModalHeader headerName={this.props.headerName} />
                <br></br>
                <form onSubmit={this.handleSubmit}>
                    <div className="form-inline">
                        <label className="input-group-text" for="autofill_id_type">
                            {this.props.selectMeta}
                        </label>
                        &nbsp;&nbsp;
                        <select name="idType" id="autofill_id_type" value={this.state.idType.value}
                            onChange={this.handleChange} className="form-control">
                            {this.state.selectOptions}
                        </select>
                        &nbsp;&nbsp;
                        <input name="itemId" type="text" id="autofill_item_id"
                            value={this.state.itemId} onChange={this.handleChange}
                            className="form-control ng-untouched ng-pristine ng-valid" />
                        <p className="text-center">
                            <input type="submit" id="autofill_item_button" value={this.props.getValue} className="btn btn-info" />
                        </p>
                    </div>
                    <br />
                    <div id="auto-fill-error-div">
                        <span id="autofill-error-message"></span>
                    </div>
                </form>
            </div>
        );
    }
}

$(function () {
    let meta_search_body = document.querySelector('#meta-search-body');
    let headerName = $("#autofill_header_name").val();
    let selectMeta = $("#autofill_select_meta").val();
    let getValue = $("#autofill_get_value").val();
    let achievement_type = $("#autofill_achievement_type").val();
    let achievement_id = $("#autofill_achievement_id").val();
    let enable_item_achievement_link = $("#autofill_enable_item_achievement_link").val();
    let cris_linkage_linked_ids = $("#cris_linkage_linked_ids").val();
    let cris_linkage_linked_message_tmp = $("#cris_linkage_linked_message").val();
    let cris_linkage_linked_message = cris_linkage_linked_message_tmp.replace("{achievement_id}", cris_linkage_linked_ids);
    
    const autofill_parmalink = $("#autofill_parmalink").val();
    const autofill_published_papers = $("#autofill_published_papers").val();
    const autofill_misc = $("#autofill_misc").val();
    const autofill_books_etc = $("#autofill_book_etc").val();
    const autofill_presentations = $("#autofill_presentations").val();
    const autofill_works = $("#autofill_works").val();
    const autofill_others = $("#autofill_others").val();


    ReactDOM.render(
        <SearchMetaForm headerName={headerName}
            selectMeta={selectMeta}
            getValue={getValue} 
            achievement_type={achievement_type}
            achievement_id={achievement_id}
            enable_item_achievement_link={enable_item_achievement_link}
            cris_linkage_linked_ids={cris_linkage_linked_ids}
            cris_linkage_linked_message={cris_linkage_linked_message}
            autofill_parmalink={autofill_parmalink}
            autofill_published_papers={autofill_published_papers}
            autofill_misc={autofill_misc}
            autofill_books_etc={autofill_books_etc}
            autofill_presentations={autofill_presentations}
            autofill_works={autofill_works}
            autofill_others={autofill_others}
            />,
        meta_search_body
    )
});
