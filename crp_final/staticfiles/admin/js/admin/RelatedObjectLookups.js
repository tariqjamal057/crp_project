/*global SelectBox, interpolate*/
// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
<<<<<<< HEAD
'use strict';
{
    const $ = django.jQuery;
    let popupIndex = 0;
    const relatedWindows = [];

    function dismissChildPopups() {
        relatedWindows.forEach(function(win) {
            if(!win.closed) {
                win.dismissChildPopups();
                win.close();    
            }
        });
    }

    function setPopupIndex() {
        if(document.getElementsByName("_popup").length > 0) {
            const index = window.name.lastIndexOf("__") + 2;
            popupIndex = parseInt(window.name.substring(index));   
        } else {
            popupIndex = 0;
        }
    }

    function addPopupIndex(name) {
        return name + "__" + (popupIndex + 1);
    }

    function removePopupIndex(name) {
        return name.replace(new RegExp("__" + (popupIndex + 1) + "$"), '');
    }

    function showAdminPopup(triggeringLink, name_regexp, add_popup) {
        const name = addPopupIndex(triggeringLink.id.replace(name_regexp, ''));
        const href = new URL(triggeringLink.href);
        if (add_popup) {
            href.searchParams.set('_popup', 1);
        }
        const win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        relatedWindows.push(win);
=======

(function($) {
    'use strict';

    // IE doesn't accept periods or dashes in the window name, but the element IDs
    // we use to generate popup window names may contain them, therefore we map them
    // to allowed characters in a reversible way so that we can locate the correct
    // element when the popup window is dismissed.
    function id_to_windowname(text) {
        text = text.replace(/\./g, '__dot__');
        text = text.replace(/\-/g, '__dash__');
        return text;
    }

    function windowname_to_id(text) {
        text = text.replace(/__dot__/g, '.');
        text = text.replace(/__dash__/g, '-');
        return text;
    }

    function showAdminPopup(triggeringLink, name_regexp, add_popup) {
        var name = triggeringLink.id.replace(name_regexp, '');
        name = id_to_windowname(name);
        var href = triggeringLink.href;
        if (add_popup) {
            if (href.indexOf('?') === -1) {
                href += '?_popup=1';
            } else {
                href += '&_popup=1';
            }
        }
        // GRAPPELLI CUSTOM: changed width
        var win = window.open(href, name, 'height=500,width=1000,resizable=yes,scrollbars=yes');
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        win.focus();
        return false;
    }

    function showRelatedObjectLookupPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^lookup_/, true);
    }

    function dismissRelatedLookupPopup(win, chosenId) {
<<<<<<< HEAD
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
            elem.value += ',' + chosenId;
        } else {
            elem.value = chosenId;
        }
        $(elem).trigger('change');
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
=======
        var name = windowname_to_id(win.name);
        var elem = document.getElementById(name);
        if (elem.className.indexOf('vManyToManyRawIdAdminField') !== -1 && elem.value) {
            elem.value += ',' + chosenId;
        } else {
            document.getElementById(name).value = chosenId;
        }
        // GRAPPELLI CUSTOM: element focus
        elem.focus();
        $(elem).trigger('change');
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        win.close();
    }

    function showRelatedObjectPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
    }

    function updateRelatedObjectLinks(triggeringLink) {
<<<<<<< HEAD
        const $this = $(triggeringLink);
        const siblings = $this.nextAll('.view-related, .change-related, .delete-related');
        if (!siblings.length) {
            return;
        }
        const value = $this.val();
        if (value) {
            siblings.each(function() {
                const elm = $(this);
                elm.attr('href', elm.attr('data-href-template').replace('__fk__', value));
                elm.removeAttr('aria-disabled');
            });
        } else {
            siblings.removeAttr('href');
            siblings.attr('aria-disabled', true);
        }
    }

    function updateRelatedSelectsOptions(currentSelect, win, objId, newRepr, newId, skipIds = []) {
        // After create/edit a model from the options next to the current
        // select (+ or :pencil:) update ForeignKey PK of the rest of selects
        // in the page.

        const path = win.location.pathname;
        // Extract the model from the popup url '.../<model>/add/' or
        // '.../<model>/<id>/change/' depending the action (add or change).
        const modelName = path.split('/')[path.split('/').length - (objId ? 4 : 3)];
        // Select elements with a specific model reference and context of "available-source".
        const selectsRelated = document.querySelectorAll(`[data-model-ref="${modelName}"] [data-context="available-source"]`);

        selectsRelated.forEach(function(select) {
            if (currentSelect === select || skipIds && skipIds.includes(select.id)) {
                return;
            }

            let option = select.querySelector(`option[value="${objId}"]`);

            if (!option) {
                option = new Option(newRepr, newId);
                select.options.add(option);
                // Update SelectBox cache for related fields.
                if (window.SelectBox !== undefined && !SelectBox.cache[currentSelect.id]) {
                    SelectBox.add_to_cache(select.id, option);
                    SelectBox.redisplay(select.id);
                }
                return;
            }

            option.textContent = newRepr;
            option.value = newId;
        });
    }

    function dismissAddRelatedObjectPopup(win, newId, newRepr) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem) {
            const elemName = elem.nodeName.toUpperCase();
            if (elemName === 'SELECT') {
                elem.options[elem.options.length] = new Option(newRepr, newId, true, true);
                updateRelatedSelectsOptions(elem, win, null, newRepr, newId);
            } else if (elemName === 'INPUT') {
                if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
=======
        var $this = $(triggeringLink);
        // GRAPPELLI CUSTOM: use parent before nextAll
        var siblings = $this.parent().nextAll().find('.view-related, .change-related, .delete-related');
        if (!siblings.length) {
            return;
        }
        var value = $this.val();
        if (value) {
            siblings.each(function() {
                var elm = $(this);
                elm.attr('href', elm.attr('data-href-template').replace('__fk__', value));
            });
        } else {
            siblings.removeAttr('href');
        }
    }

    function dismissAddRelatedObjectPopup(win, newId, newRepr) {
        var name = windowname_to_id(win.name);
        var elem = document.getElementById(name);
        if (elem) {
            var elemName = elem.nodeName.toUpperCase();
            if (elemName === 'SELECT') {
                elem.options[elem.options.length] = new Option(newRepr, newId, true, true);
            } else if (elemName === 'INPUT') {
                if (elem.className.indexOf('vManyToManyRawIdAdminField') !== -1 && elem.value) {
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
                    elem.value += ',' + newId;
                } else {
                    elem.value = newId;
                }
<<<<<<< HEAD
=======
                // GRAPPELLI CUSTOM: element focus
                elem.focus();
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
            }
            // Trigger a change event to update related links if required.
            $(elem).trigger('change');
        } else {
<<<<<<< HEAD
            const toId = name + "_to";
            const toElem = document.getElementById(toId);
            const o = new Option(newRepr, newId);
            SelectBox.add_to_cache(toId, o);
            SelectBox.redisplay(toId);
            if (toElem && toElem.nodeName.toUpperCase() === 'SELECT') {
                const skipIds = [name + "_from"];
                updateRelatedSelectsOptions(toElem, win, null, newRepr, newId, skipIds);
            }
        }
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
=======
            var toId = name + "_to";
            var o = new Option(newRepr, newId);
            SelectBox.add_to_cache(toId, o);
            SelectBox.redisplay(toId);
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        }
        win.close();
    }

    function dismissChangeRelatedObjectPopup(win, objId, newRepr, newId) {
<<<<<<< HEAD
        const id = removePopupIndex(win.name.replace(/^edit_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = $(selectsSelector);
=======
        var id = windowname_to_id(win.name).replace(/^edit_/, '');
        var elem = document.getElementById(id);
        var selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        var selects = $(selectsSelector);
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        selects.find('option').each(function() {
            if (this.value === objId) {
                this.textContent = newRepr;
                this.value = newId;
            }
<<<<<<< HEAD
        }).trigger('change');
        updateRelatedSelectsOptions(selects[0], win, objId, newRepr, newId);
=======
        });
        // GRAPPELLI CUSTOM: element focus
        elem.focus();
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        selects.next().find('.select2-selection__rendered').each(function() {
            // The element can have a clear button as a child.
            // Use the lastChild to modify only the displayed value.
            this.lastChild.textContent = newRepr;
            this.title = newRepr;
        });
<<<<<<< HEAD
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
=======
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        win.close();
    }

    function dismissDeleteRelatedObjectPopup(win, objId) {
<<<<<<< HEAD
        const id = removePopupIndex(win.name.replace(/^delete_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = $(selectsSelector);
=======
        var id = windowname_to_id(win.name).replace(/^delete_/, '');
        var elem = document.getElementById(id);
        var selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        var selects = $(selectsSelector);
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        selects.find('option').each(function() {
            if (this.value === objId) {
                $(this).remove();
            }
        }).trigger('change');
<<<<<<< HEAD
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

=======
        // GRAPPELLI CUSTOM: element focus
        elem.focus();
        win.close();
    }

    // GRAPPELLI CUSTOM
    function removeRelatedObject(triggeringLink) {
        var id = triggeringLink.id.replace(/^remove_/, '');
        var elem = document.getElementById(id);
        elem.value = "";
        elem.focus();
    }
    window.removeRelatedObject = removeRelatedObject;

    // Global for testing purposes
    window.id_to_windowname = id_to_windowname;
    window.windowname_to_id = windowname_to_id;

>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
    window.showRelatedObjectLookupPopup = showRelatedObjectLookupPopup;
    window.dismissRelatedLookupPopup = dismissRelatedLookupPopup;
    window.showRelatedObjectPopup = showRelatedObjectPopup;
    window.updateRelatedObjectLinks = updateRelatedObjectLinks;
    window.dismissAddRelatedObjectPopup = dismissAddRelatedObjectPopup;
    window.dismissChangeRelatedObjectPopup = dismissChangeRelatedObjectPopup;
    window.dismissDeleteRelatedObjectPopup = dismissDeleteRelatedObjectPopup;
<<<<<<< HEAD
    window.dismissChildPopups = dismissChildPopups;
    window.relatedWindows = relatedWindows;
=======
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723

    // Kept for backward compatibility
    window.showAddAnotherPopup = showRelatedObjectPopup;
    window.dismissAddAnotherPopup = dismissAddRelatedObjectPopup;

<<<<<<< HEAD
    window.addEventListener('unload', function(evt) {
        window.dismissChildPopups();
    });

    $(document).ready(function() {
        setPopupIndex();
=======
    $(document).ready(function() {
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
        $("a[data-popup-opener]").on('click', function(event) {
            event.preventDefault();
            opener.dismissRelatedLookupPopup(window, $(this).data("popup-opener"));
        });
<<<<<<< HEAD
        $('body').on('click', '.related-widget-wrapper-link[data-popup="yes"]', function(e) {
            e.preventDefault();
            if (this.href) {
                const event = $.Event('django:show-related', {href: this.href});
=======
        $('body').on('click', '.related-widget-wrapper-link', function(e) {
            e.preventDefault();
            if (this.href) {
                var event = $.Event('django:show-related', {href: this.href});
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
                $(this).trigger(event);
                if (!event.isDefaultPrevented()) {
                    showRelatedObjectPopup(this);
                }
            }
        });
        $('body').on('change', '.related-widget-wrapper select', function(e) {
<<<<<<< HEAD
            const event = $.Event('django:update-related');
=======
            var event = $.Event('django:update-related');
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
            $(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                updateRelatedObjectLinks(this);
            }
        });
<<<<<<< HEAD
        $('.related-widget-wrapper select').trigger('change');
        $('body').on('click', '.related-lookup', function(e) {
            e.preventDefault();
            const event = $.Event('django:lookup-related');
=======
        // GRAPPELLI CUSTOM
        /* triggering select means that update_lookup is triggered with
        generic autocompleted (which would empty the field) */
        $('.grp-related-widget-tools').parent().children('.grp-related-widget').children('select:first-child').trigger('change');
        $('body').on('click', '.related-lookup', function(e) {
            e.preventDefault();
            var event = $.Event('django:lookup-related');
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
            $(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                showRelatedObjectLookupPopup(this);
            }
        });
    });
<<<<<<< HEAD
}
=======

})(grp.jQuery);
>>>>>>> d15895bcda58e9e5a1a3241ac2e73535be307723
