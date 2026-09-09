/*
 * This file is part of WEKO3.
 * Copyright (C) 2017 National Institute of Informatics.
 */

import $ from 'jquery';
import 'bootstrap';
import '../node_modules/select2/dist/js/select2.full.js';

// Pass a copied $ to functions using require(Must specify in files)
const noConflictjQuery = $.noConflict(true);

export { noConflictjQuery };
