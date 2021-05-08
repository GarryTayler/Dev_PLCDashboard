const limitMsg = "더이상 등록할수 없습니다";
const saveMsg = "저장하였습니다";
const refreshMsg = "브라우저 리프레쉬 후 다시 시도해주세요";
const timeFormat = "9999:99:99:999";

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

const infoCallback = function( settings, start, end, max, total, pre ) {
                    let api = this.api();
                    if(parseInt(total) > 0)
                        return "전체 " + numberWithCommas(total) + " 개중 " + numberWithCommas(start) + " 부터 " + numberWithCommas((  (total > start + parseInt(api.page.info().length) - 1) ? (start + parseInt(api.page.info().length) - 1) : (total)  )) + " 까지 표시";
                    else
                        return "표시할 데이터가 없습니다.";
};

const dataTableLang = {
    "language": {
        "decimal":        "",
        "emptyTable":     "데이터 없음",
        "info":           "전체 _TOTAL_ 개중 _START_ 부터 _END_ 까지 표시",
        "infoEmpty":      "데이터 없음",
        "infoPostFix":    "",
        "thousands":      ",",
        "infoFiltered":  "",
        "lengthMenu":     "_MENU_ 개행",
        "loadingRecords": "로딩중...",
        "processing":     "로딩중...",
        "paginate": {
            "next": "다음",
            "last": "마감",
            "first": "시작",
            "previous": "이전"
        },
        "search": "검색:",
        "zeroRecords": "일치하는 레코드를 찾을 수 없습니다"
    }
};
const dataTableObj = {
    // 'lengthMenu': [ [5, 10, 25, 50], [5, 10, 25, 50] ],
    'bAutoWidth': false,
    'processing': true,
    'serverSide': true,
    'serverMethod': 'post',
    'ordering': false,
    'searching': true,
    'iDisplayLength': localStorage.getItem('page-cnt') ? localStorage.getItem('page-cnt') : 10
};
const columnDef = [{
    "className": 'text-center',
    "targets": 0
}];
const spectrumObj = {
    type: "component",
    showInput: true
};
const checkForm = `
    <div class="form-check">
        <input type="checkbox" class="form-check-input check-row" id="check-row-data.id" data.attr>
        <label class="form-check-label"></label>
    </div>
`;

let dataTables;
const headerImg = $(".header-img");
const curMode = headerImg.attr('mode');
const curAuth = headerImg.attr('edit') === "True";
const csrf_token = $("#csrf_token").val().trim();

function addZero(str) {
    return ("0" + str).slice(-2);
}

function showHeaderTime() {
    let date = new Date().toLocaleDateString('en-US', {timeZone: 'Asia/Tokyo'});
    let time = new Date().toLocaleTimeString('en-US', {timeZone: 'Asia/Tokyo'});
    date = date.split("/");
    date = date[2] + "-" + addZero(date[0]) + "-" + addZero(date[1]);

    const ampm = time.slice(-2);
    const timeArr = time.substr(0, time.length - 3).split(":");
    time = ampm === "AM" ? addZero(timeArr[0]) : addZero(parseInt(timeArr[0]) + 12);
    time += ":" + addZero(timeArr[1]) + ":" + addZero(timeArr[2]);

    $("#current-date").text(date);
    $("#current-time").text(time);
}

function input_val(inputID) {
    const selInput = $("#" + inputID);
    const inputVal = selInput.val().trim();
    if(inputVal.length === 0) {
        showErr(inputID);
        return false;
    } else {
        return inputVal;
    }
}

function showErr(inputID) {
    const idInput = $("#" + inputID);
    idInput.addClass('border-danger');
    idInput.closest('div.modal-body').find('div.insert-alert').show();
}

function sendAjax(url, data, refresh = true, isFile = false, respFunc = null) {
    const processFile = isFile ? {processData: false, contentType: false} : {};
    $.ajax({
        url: url,
        type: 'POST',
        dataType: 'json',
        headers: { "X-CSRFToken": csrf_token },
        data: data,
        ...processFile,
        success: function(resp) {
            if(respFunc) {
                respFunc(resp);
            } else {
                if(resp.status) {
                    if(dataTables) {
                        localStorage.setItem('page-cnt', dataTables.page.info().length);
                    }

                    if(refresh) {
                        location.reload();
                    }
                } else {
                    alert(resp.message);
                }
            }
        },
        error: function(err) {
            console.log("error=====", err);
            alert(refreshMsg);
        }
    });
}

function initAltInput(selItem, options, prefixStr = "") {
    const parentDiv = selItem.closest('div.value-radio');
    const curChk = parentDiv.find("input[type='checkbox']");
    const inputGroup = parentDiv.find('div.input-group');
    const groupInput = inputGroup.find('input.form-control');
    const selectInput = parentDiv.find('.alt-input');
    const attrName = selectInput.attr('type') ? 'id' : 'name';
    const repStr = selectInput.attr('type') ? '-' : '_';

    let inputID = selectInput.attr('name') || selectInput.attr('id') ? (selectInput.attr('id') ? selectInput.attr('id') : selectInput.attr('name')) : (groupInput.attr('id') ? groupInput.attr('id') : groupInput.attr('name'));
    inputID = inputID.replaceAll('_', '-').replace(prefixStr, '');
    const inputID1 = inputID.replaceAll("-", "_");

    if(options.hasOwnProperty((inputID1 + "_selid")) ||
        !(options[inputID1] && options[inputID1].length > 0)) {
        curChk.prop('checked', true);
        inputGroup.show();
        groupInput.attr('id', inputID);
        selectInput.hide().removeAttr(attrName);
    } else {
        curChk.prop('checked', false);
        inputGroup.hide();
        selectInput.attr(attrName, inputID.replaceAll('-', repStr)).show();
        groupInput.removeAttr('id');
    }
}

function initInputs(selType= '', options={}, prefixStr = "") {
    const typeInputs = $(selType + " input," + selType + " select," + selType + " textarea");
    for(let ii = 0; ii < typeInputs.length; ii++) {
        const inputItem = $(typeInputs[ii]);

        if(inputItem.closest('div.value-radio').length > 0) {
            initAltInput(inputItem, options, prefixStr);
        }

        if(!inputItem.attr('id') && !inputItem.attr('name')) continue;

        const inputID = inputItem.attr('name') ? inputItem.attr('name') : inputItem.attr('id').replaceAll('-', '_');

        for(let optionKey in options) {
            if(!options.hasOwnProperty(optionKey)) continue;

            if(optionKey.indexOf(inputID) >= 0) {
                if(optionKey === inputID) {
                    if(inputItem.hasClass('mask-time')) {
                        inputItem.inputmask("remove");
                        inputItem.val(options[optionKey]).inputmask({format: options[optionKey]});
                    } else {
                        inputItem.val(options[optionKey]);
                    }
                } else {
                    const attrStr = optionKey.replaceAll(inputID + "_", "");
                    inputItem.attr(attrStr, options[optionKey]);
                }
            }
        }
    }
}

function getTblChk(tableID, suffix = '') {
    const rowArr = $(tableID + " tbody input.check-row").filter(':checked');
    const totalCnt = rowArr.length;
    let selIDs = [];
    if(totalCnt > 0) {
        for (let ii = 0; ii < totalCnt; ii++) {
            const itemRow = rowArr[ii];
            const itemID = $(itemRow).attr('id').replace('check-row-' + suffix, '');
            selIDs.push(itemID);
        }
    }

    return selIDs.length > 0 ? selIDs.join(',') : "";
}

function removeAction(tableID, url, suffix = '', flag = true) {
    const selRow = getTblChk(tableID, suffix);
    if(selRow.length > 0) {
        if(confirm('삭제하시겠습니까?')) {
            sendAjax(url, {selRow}, flag);
        }
    } else {
        alert('삭제할 행을 선택하세요');
    }
}

function updateVariable(selTbl = dataTables, flag = false) {
    if(selTbl) selTbl.ajax.reload(null, flag);
}

function removeCustom(tableID, url, replaceStr = '', customData = {}, refresh = true) {
    const rowArr = $(tableID + " input.check-row").filter(':checked');
    const totalCnt = rowArr.length;
    if(totalCnt > 0) {
        let selIDs = [];
        for(let ii = 0; ii < totalCnt; ii++) {
            const itemRow = rowArr[ii];
            const itemID = $(itemRow).attr('id').replace('check-row-' + replaceStr, '');
            selIDs.push(itemID);
        }

        if(selIDs.length > 0) {
            if(confirm('삭제하시겠습니까?')) {
                sendAjax(url, {...customData, selRow: selIDs.join(',')}, refresh);
            }
        }
    } else {
        alert('삭제할 행을 선택하세요.');
    }
}

function getPostData(panelID) {
    let postData = {};
    const inputArr = $(panelID + " input," + panelID + " select, " + panelID + " textarea");
    for(let ii = 0; ii < inputArr.length; ii++) {
        const inputItem = $(inputArr[ii]);

        if(!inputItem.attr('id') && !inputItem.attr('name')) continue;

        const selKey = inputItem.attr('id').replaceAll('-', '_');
        postData[selKey] = inputItem.val();
        if(inputItem.attr('selid')) {
            postData[selKey + '_selid'] = inputItem.attr('selid');
            postData[selKey + '_seltype'] = inputItem.attr('seltype');
            postData[selKey + '_sellocstr'] = inputItem.attr('sellocstr');   
            if( !(inputItem.attr("deviceid") == null || inputItem.attr("deviceid") == '' || inputItem.attr("deviceid") == undefined) ) {
                postData[selKey + "_deviceid"] = inputItem.attr("deviceid");
                postData[selKey + "_change_sellocstr"] = inputItem.attr("change_sellocstr");
            }
        }
    }

    return postData;
}

function showAddMonitor() {
    $("#monitor-alert").val('');
    $("#monitor-modal").attr('selid', '0').modal('show');
}

function showAddLogic(selID) {
    const nameInput = $("#logic-name");
    nameInput.removeClass('border-danger');
    if(selID == null || selID == undefined || selID.length < 2) {
        nameInput.val('');
        selID = '0';
    } else {
        const logicItem = $("#logic-item-" + selID);
        nameInput.val(logicItem.attr('data-name'));
        $("#logic-mode").val(logicItem.attr('mode'));
        $("#ckbx-style-1-1-logic").prop('checked', logicItem.attr('useflag') === "1");
    }

    $("#new-logic-modal").attr('selid', selID).modal('show');
}

function changeMode() {
    const headerImg = $('.header-img');
    const selMode = headerImg.attr('mode');
    if(selMode === "stop") {
        headerImg.attr('mode', 'run');
    } else {
        headerImg.attr('mode', 'stop');
    }

    sendAjax(headerImg.attr('url'), {selMode});
}

function removeDisable(str='', selMode = 'stop') {
    return curMode === selMode && curAuth ? str.replaceAll('disabled', '') : str;
}

function setDataTblPage(tblInst, dispLen) {
    tblInst.attr('before_clicked', '0');
    localStorage.setItem('page-cnt', dispLen);

    const curPage = localStorage.getItem('cur-page');
    if(dataTables && curPage && curPage > 0) {
        localStorage.removeItem('cur-page');
        dataTables.page(parseInt(curPage));
        updateVariable();
    }
}

function setVariableDataTblPage(tblInst, dispLen) {
    tblInst.attr('before_clicked', '0');
    localStorage.setItem('page-cnt', dispLen);

    //const curPage = curPage;
    if(variableInst && curPage && curPage > 0) {
        localStorage.removeItem('variable-modal-cur-page');
        variableInst.page(parseInt(curPage));
        updateVariable();
    }
}

function setDataVariableTblPage(tblInst, dispLen) {

    tblInst.attr('before_clicked', '0');
    localStorage.setItem('page-cnt', dispLen);

    const curPage = localStorage.getItem('variable-cur-page');
    if(dataTables && curPage && curPage > 0) {
        localStorage.removeItem('variable-cur-page');
        dataTables.page(parseInt(curPage));
        updateVariable();
    }
}

function setDataRemoteVariableTblPage(tblInst, dispLen) {
    tblInst.attr('before_clicked', '0');
    localStorage.setItem('page-cnt', dispLen);

    const curPage = localStorage.getItem('remote-vcur-page');

    if(dataTables && curPage && curPage > 0) {
        localStorage.removeItem('remote-vcur-page');
        dataTables.page(parseInt(curPage));
        updateVariable();
    }
}

function initTimeMask(parentDiv = '') {
    const maskArr = $(parentDiv + " .mask-time");
    for(let ii = 0; ii < maskArr.length; ii++) {
        const maskItem = $(maskArr[ii]);
        const maskVal = maskItem.attr('value');

        if(maskVal) {
            maskItem.inputmask({format: maskVal});
        } else {
            maskItem.inputmask(timeFormat);
        }
    }

    const selectArr = $(parentDiv + " select.alt-input");
    for(let ii = 0; ii < selectArr.length; ii++) {
        const selItem = $(selectArr[ii]);
        const selVal = selItem.attr('value');

        if(selVal) {
            selItem.val(selVal);
        }
    }

    $(parentDiv + " input.date-picker").datetimepicker({
        format: 'YYYY-MM-DD',
    });

    const altInputs = $("div.value-radio input[type='checkbox']");
    altInputs.unbind('click');
    altInputs.on('click', function() {
        doAltInput($(this));
    });
}

function doAltInput(selItem) {
    const curVal = selItem.prop('checked');
    const parentDiv = selItem.closest('div.value-radio');
    const inputGroup = parentDiv.find('div.input-group');
    const groupInput = inputGroup.find('input.form-control');
    const selectInput = parentDiv.find('.alt-input');
    const attrName = selectInput.attr('type') ? 'id' : 'name';
    const repStr = selectInput.attr('type') ? '-' : '_';
    if(curVal) {
        inputGroup.show();
        groupInput.attr('id', selectInput.attr(attrName).replaceAll(repStr, '-'))
        selectInput.hide().removeAttr(attrName);
    } else {
        inputGroup.hide();
        selectInput.attr(attrName, groupInput.attr('id').replaceAll('-', repStr)).show();
        groupInput.removeAttr('id');
    }
    if(!(selItem.attr('recipe') == undefined || selItem.attr('recipe') == '' || selItem.attr('recipe') == null))
        updateRecipeVariable(selItem);
}

$(document).ready(function() {
    setInterval(function () {
        showHeaderTime();
    }, 1000);

    $(".check-all").on('click', function () {
        const selTbl = $(this).closest('table').attr('id');
        const selChk = selTbl && selTbl.length > 0 ? "#" + selTbl + " .check-row" : ".check-row";
        const checked = $(this).prop('checked');
        $(selChk).prop("checked", checked);
    });

    const tooltips = $('[data-toggle="tooltip"]');
    if(tooltips.length > 0) {
        tooltips.tooltip({trigger: 'hover'});
    }

    $("#monitor-add-btn").on('click', function () {
        const buildInput = $("#monitor-name");
        const alertInput = $("#monitor-alert");
        alertInput.addClass('display-none');
        buildInput.removeClass('border-danger');

        const input_name = buildInput.val().trim();
        if(input_name.length > 0) {
            const inputID = $("#monitor-modal").attr('selid');
            const respFunc = function(resp) {
                if(resp.status) {
                    if(parseInt(inputID) > 0) {
                        location.reload();
                    } else {
                        location.href = "/monitor/detail/" + resp.selid;
                    }
                } else {
                    alert(resp.message);
                }
            }

            sendAjax("/monitor/add_monitor", { input_name, inputID }, false, false, respFunc);
        } else {
            buildInput.addClass('border-danger');
            alertInput.removeClass('display-none');
        }
    });

    $("#logic-add-btn").on('click', function() {
        const nameInput = $("#logic-name");
        const logicName = nameInput.val().trim();
        if(logicName.length > 0) {
            const selID = $("#new-logic-modal").attr('selid');
            const postData = {
                name: logicName,
                mode: $("#logic-mode").val(),
                selid: selID,
                use_flag: $("#ckbx-style-1-1-logic").prop('checked') ? '1' : '0'
            };

            const respFunc = function(resp) {
                if(resp.status) {
                    if(selID.length > 1) {
                        location.reload();
                    } else {
                        location.href = "/logic_build/logic/" + resp.selid;
                    }
                } else {
                    alert(resp.message);
                }
            }
            sendAjax($(this).attr('data-url'), postData, false, false, respFunc);
        } else {
            nameInput.addClass('border-danger');
            alert('이름을 입력하세요');
        }
    });

    $("#collapsePages a.collapse-item, #collapseTwo a.collapse-item").hover(function() {
        $(this).find('i.build-remove-icon').show();
    }, function() {
        $(this).find('i.build-remove-icon').hide();
    });

    $("i.build-remove-detail-icon").on('click', function(e) {
        e.preventDefault();    
        if(confirm('삭제하시겠습니까?')) {
            let urlArr = $(this).attr('detailurl').trim().split('/');
            urlArr[2] = "remove_" + urlArr[2];
            const selRow = urlArr[3];
            urlArr.splice(-1, 1);
            const urlStr = urlArr.join('/');
            sendAjax(urlStr, {selRow});
        }
    });

    $(document).on('contextmenu', function(e) {
        const parentTr = $(e.target).closest('tr');
        const parentTbody = $(e.target).closest('tbody');
        const parentAch = $(e.target).closest('a.header-alarm');
        const parentTable = $(e.target).closest('table');

        let contextMenu = null;
        $(".contextmenu").hide();
        if ((parentTbody.length > 0 && !parentTable.hasClass('no-context')) ||
            parentAch.length > 0) {
            e.preventDefault();
            e.stopPropagation();

            if(parentTable.attr('edit')) {
                $("#contextmenu-edit").hide();
            } else {
                $("#contextmenu-edit").show();
            }

            if(parentTable.attr('build')) {
                $("#contextmenu-build").show();
            } else {
                $("#contextmenu-build").hide();
            }

            contextMenu = $("#contextmenu")
                .attr('seltbl', parentTable.attr('id'))
                .attr('selrow', parentTr.attr('data-row'));
            $("#alarmMenu").hide();
        } else if(parentTable.attr('id') === "recipe-val-table" && curMode === "stop") {
            contextMenu = $("#recipe-context");
        }

        if(contextMenu) {
            contextMenu.css({
                top: e.pageY + 'px',
                left: e.pageX + 'px'
            }).show();

            return false;
        } else {
            return true;
        }
    });

    $(document).on('click', function(e) {
        $('.contextmenu').hide();
    });

    $(".header-alarm").on('dblclick', function () {
        location.href = "/user/alarms";
    });

    $(".modal-body, #variable-tbody").on("blur", "input[type='text']", function() {
        if(!$(this).attr('readonly')) {
            const currentVal = $(this).val().trim();
            let originVal = $(this).attr('origin');
            originVal = originVal && originVal.length > 0 ? originVal : '';
            if(originVal !== currentVal) {
                $(this).attr('origin', currentVal).removeAttr('selid').removeAttr('seltype').removeAttr('sellocstr').trigger('change');
            }
        }
    });

    $(window).bind("beforeunload", function() {
        if(dataTables) {
            localStorage.setItem('cur-page', dataTables.page.info().page);
        }
    });

    $("div.value-radio input[type='checkbox']").on('click', function() {
        doAltInput($(this));
    });
});