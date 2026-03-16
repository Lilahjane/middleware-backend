/**
 * Just Meal Planner - Frontend Application
 * 
 * Handles:
 * - Recipe scraping via /scrape endpoint
 * - Recipe ID assignment via /assign-recipe-id endpoint
 * - Ingredient normalization display
 * - Yield scaling calculations
 * - Grocery list aggregation and display
 */

// ============================================================================
// CONFIGURATION & STATE
// ============================================================================

const API_BASE = 'http://localhost:5000';

let appState = {
    currentRecipe: null,
    currentRecipeId: null,
    normalizedIngredients: null,
    scaleFactor: 1,
    originalServings: 4,
    currentUrl: null,
    recentErrors: [],
    allRecipes: []
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function () {
    console.log('Just Meal Planner UI initialized');

    // Setup event listeners
    document.getElementById('scrapeBtn').addEventListener('click', scrapeRecipe);
    document.getElementById('urlInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') scrapeRecipe();
    });

    document.getElementById('assignIdBtn').addEventListener('click', assignRecipeId);
    document.getElementById('servingScale').addEventListener('change', handleServingChange);

    // Check API status
    checkApiStatus();
});

// ============================================================================
// API STATUS & HEALTH CHECK
// ============================================================================

async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        updateApiStatus('ok', 'Connected to API');
        appState.recentErrors = data.recent_errors || [];

        console.log('API Status:', data);
    } catch (error) {
        updateApiStatus('error', 'Cannot connect to API');
        console.error('API Status Check Failed:', error);
    }
}

function updateApiStatus(status, message) {
    const statusEl = document.getElementById('apiStatus');
    statusEl.className = `status-indicator ${status}`;
    statusEl.textContent = message;
}

// ============================================================================
// SECTION 1: RECIPE SCRAPING
// ============================================================================

async function scrapeRecipe() {
    const url = document.getElementById('urlInput').value.trim();

    if (!url) {
        showError('validation_error', 'Please enter a recipe URL');
        return;
    }

    appState.currentUrl = url;

    // Show progress
    const progressEl = document.getElementById('scrapeProgress');
    progressEl.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, timeout: 30 })
        });

        const data = await response.json();
        progressEl.classList.add('hidden');

        if (data.error) {
            // Handle error response from API
            showError(data.error_type, data.error_message, data.error_id, data.timestamp, url);
            return;
        }

        // Success: Store recipe and proceed
        appState.currentRecipe = data.recipe;
        appState.normalizedIngredients = data.recipe.ingredients || [];

        // Show raw JSON
        displayRawRecipeJson(data.recipe);

        // Clear any previous errors
        clearError();

        // Show recipe confirmation
        displayRecipeConfirmation(data.recipe);

        console.log('Recipe scraped successfully:', data.recipe.title);

    } catch (error) {
        progressEl.classList.add('hidden');
        showError('scraper_error', `Network error: ${error.message}`);
        console.error('Scrape Error:', error);
    }
}

function displayRawRecipeJson(recipe) {
    const container = document.getElementById('recipeRawData');
    const preEl = document.getElementById('rawRecipeJson');

    preEl.textContent = JSON.stringify(recipe, null, 2);
    container.classList.remove('hidden');
}

// ============================================================================
// SECTION 2: ERROR HANDLING & DISPLAY
// ============================================================================

function showError(errorType, errorMessage, errorId = null, timestamp = null, sourceUrl = null) {
    const errorDisplay = document.getElementById('errorDisplay');

    document.getElementById('errorType').textContent = errorType || 'UNKNOWN_ERROR';
    document.getElementById('errorMessage').textContent = errorMessage;

    if (errorId) {
        document.getElementById('errorId').textContent = errorId;
    }

    if (timestamp) {
        const date = new Date(timestamp);
        document.getElementById('errorTimestamp').textContent = date.toLocaleString();
    }

    if (sourceUrl) {
        const urlDisplay = document.getElementById('urlDisplay');
        document.getElementById('errorUrl').textContent = sourceUrl;
        urlDisplay.classList.remove('hidden');
    }

    errorDisplay.classList.remove('hidden');

    // Update error count
    updateErrorCount();
}

function clearError() {
    document.getElementById('errorDisplay').classList.add('hidden');
}

function updateErrorCount() {
    const errorCount = appState.recentErrors.length;
    document.getElementById('errorCount').textContent = `${errorCount} error${errorCount !== 1 ? 's' : ''}`;
}

function retryLastUrl() {
    if (appState.currentUrl) {
        document.getElementById('urlInput').value = appState.currentUrl;
        scrapeRecipe();
    }
}

// ============================================================================
// SECTION 3: RECIPE CONFIRMATION & ID ASSIGNMENT
// ============================================================================

function displayRecipeConfirmation(recipe) {
    const confirmation = document.getElementById('recipeConfirmation');

    document.getElementById('recipeTitleDisplay').textContent = recipe.title || 'Unknown Recipe';

    const imageEl = document.getElementById('recipeImageDisplay');
    if (recipe.image) {
        imageEl.src = recipe.image;
    }

    document.getElementById('yieldDisplay').textContent = recipe.yields || 'Not specified';
    document.getElementById('cookTimeDisplay').textContent = recipe.cook_time || 'Not specified';
    document.getElementById('prepTimeDisplay').textContent = recipe.prep_time || 'Not specified';
    document.getElementById('cuisineDisplay').textContent = recipe.cuisine || 'Not specified';

    // Store original servings for scaling
    const yieldMatch = (recipe.yields || '4').match(/\d+/);
    appState.originalServings = yieldMatch ? parseInt(yieldMatch[0]) : 4;

    confirmation.classList.remove('hidden');
}

async function assignRecipeId() {
    if (!appState.currentRecipe) {
        showError('validation_error', 'No recipe to assign ID to');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/assign-recipe-id`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                recipe_json: appState.currentRecipe,
                recipe_url: appState.currentUrl
            })
        });

        const data = await response.json();

        if (data.error) {
            showError('validation_error', data.error_message);
            return;
        }

        // Success: Store recipe ID and update UI
        appState.currentRecipeId = data.recipe_id;
        appState.allRecipes.push({
            id: data.recipe_id,
            title: appState.currentRecipe.title,
            recipe: appState.currentRecipe
        });

        document.getElementById('assignedRecipeId').textContent = data.recipe_id;
        document.getElementById('idAssignment').classList.remove('hidden');

        // Now show ingredient normalization and scaling
        displayIngredientNormalization(appState.currentRecipe.ingredients || []);
        displayScalingControls();
        displayGroceryListControls();

        console.log('Recipe ID assigned:', data.recipe_id);

    } catch (error) {
        showError('scraper_error', `Error assigning ID: ${error.message}`);
        console.error('ID Assignment Error:', error);
    }
}

function clearRecipe() {
    appState.currentRecipe = null;
    appState.currentRecipeId = null;

    document.getElementById('recipeConfirmation').classList.add('hidden');
    document.getElementById('idAssignment').classList.add('hidden');
    document.getElementById('ingredientTable').classList.add('hidden');
    document.getElementById('scalingControls').classList.add('hidden');
    document.getElementById('groceryListControls').classList.add('hidden');
}

// ============================================================================
// SECTION 4: INGREDIENT NORMALIZATION
// ============================================================================

function displayIngredientNormalization(ingredients) {
    const tableBody = document.getElementById('ingredientTableBody');
    tableBody.innerHTML = '';

    let unresolvedCount = 0;

    // For demo: simulate ingredient normalization
    ingredients.forEach((ingredient) => {
        const row = document.createElement('tr');

        // Simulate normalization (in real implementation, this would come from the API)
        const normalized = simulateIngredientNormalization(ingredient);

        if (!normalized.ingredient_id) {
            unresolvedCount++;
        }

        row.innerHTML = `
            <td>${ingredient}</td>
            <td>${normalized.canonical_name || ingredient}</td>
            <td><code>${normalized.ingredient_id || 'unresolved'}</code></td>
            <td>${normalized.confidence || 'low'}</td>
        `;

        tableBody.appendChild(row);
    });

    // Show unresolved warning if needed
    const unresolvedWarning = document.getElementById('unresolvedCount');
    if (unresolvedCount > 0) {
        unresolvedWarning.textContent = `⚠️ ${unresolvedCount} unresolved ingredient${unresolvedCount !== 1 ? 's' : ''} - needs manual verification`;
        unresolvedWarning.classList.remove('hidden');
    } else {
        unresolvedWarning.classList.add('hidden');
    }

    document.getElementById('ingredientTable').classList.remove('hidden');
}

function simulateIngredientNormalization(ingredientString) {
    // Simple simulation - in real app, this would call the normalization API
    // This demonstrates the data structure

    const lowerIngredient = ingredientString.toLowerCase();

    // Mock ingredient registry lookups
    const registry = {
        'flour': { name: 'Flour, All-Purpose', id: 'ing_flour_all_purpose_001', confidence: 'high' },
        'sugar': { name: 'Sugar, Granulated', id: 'ing_sugar_granulated_001', confidence: 'high' },
        'butter': { name: 'Butter, Unsalted', id: 'ing_butter_unsalted_001', confidence: 'high' },
        'egg': { name: 'Egg, Whole', id: 'ing_egg_whole_001', confidence: 'high' },
        'salt': { name: 'Salt, Table', id: 'ing_salt_table_001', confidence: 'high' },
        'ham': { name: 'Ham, Jamón Serrano', id: 'ing_ham_serrano_001', confidence: 'high' },
    };

    for (const [key, value] of Object.entries(registry)) {
        if (lowerIngredient.includes(key)) {
            return {
                canonical_name: value.name,
                ingredient_id: value.id,
                confidence: value.confidence
            };
        }
    }

    // Return unresolved
    return {
        canonical_name: ingredientString,
        ingredient_id: null,
        confidence: 'low'
    };
}

// ============================================================================
// SECTION 5: YIELD SCALING
// ============================================================================

function displayScalingControls() {
    document.getElementById('scalingControls').classList.remove('hidden');
    updateScaling();
}

function handleServingChange(e) {
    const value = e.target.value;
    const customInput = document.getElementById('customServings');

    if (value === 'custom') {
        customInput.classList.remove('hidden');
        customInput.focus();
    } else {
        customInput.classList.add('hidden');
        appState.scaleFactor = parseInt(value) / appState.originalServings;
        updateScaling();
    }
}

function updateScaling() {
    const customServings = document.getElementById('customServings').value;

    if (customServings) {
        appState.scaleFactor = parseInt(customServings) / appState.originalServings;
    }

    const tableBody = document.getElementById('scalingTableBody');
    tableBody.innerHTML = '';

    const ingredients = appState.currentRecipe.ingredients || [];

    ingredients.forEach((ingredient) => {
        const row = document.createElement('tr');

        // Simple scaling calculation
        const scaled = scaleIngredient(ingredient, appState.scaleFactor);

        row.innerHTML = `
            <td>${ingredient}</td>
            <td>${ingredient}</td>
            <td>${scaled}</td>
            <td>× ${appState.scaleFactor.toFixed(2)}</td>
        `;

        tableBody.appendChild(row);
    });
}

function scaleIngredient(ingredientString, factor) {
    // Extract number and unit, scale the number
    const match = ingredientString.match(/(\d+\.?\d*)\s*(\w+)?\s*(.*)/);

    if (match && match[1]) {
        const amount = parseFloat(match[1]);
        const unit = match[2] || '';
        const name = match[3] || '';

        const scaled = (amount * factor).toFixed(2);

        return `${scaled} ${unit} ${name}`.trim();
    }

    return ingredientString;
}

// ============================================================================
// SECTION 6: GROCERY LIST
// ============================================================================

function displayGroceryListControls() {
    document.getElementById('groceryListControls').classList.remove('hidden');
    document.getElementById('recipeCount').textContent = appState.allRecipes.length;
}

function generateGroceryList() {
    const groceryList = aggregateIngredients(appState.allRecipes);
    displayGroceryList(groceryList);
}

function aggregateIngredients(recipes) {
    const aggregated = {};

    recipes.forEach((recipeData) => {
        const ingredients = recipeData.recipe.ingredients || [];

        ingredients.forEach((ingredient) => {
            if (!aggregated[ingredient]) {
                aggregated[ingredient] = 0;
            }
            aggregated[ingredient]++;
        });
    });

    return aggregated;
}

function displayGroceryList(groceryList) {
    const categoriesContainer = document.getElementById('groceryCategories');
    categoriesContainer.innerHTML = '';

    // Group by category (simple categorization for demo)
    const categories = categorizIngredients(groceryList);

    Object.entries(categories).forEach(([category, items]) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'grocery-category';

        let itemsHtml = `<h4>${category}</h4>`;

        items.forEach((item) => {
            const itemId = `grocery-${Math.random().toString(36).substr(2, 9)}`;
            itemsHtml += `
                <div class="grocery-item">
                    <input type="checkbox" id="${itemId}">
                    <label for="${itemId}">
                        <span>${item.name}</span>
                        <span class="grocery-quantity">${item.count > 1 ? `× ${item.count}` : ''}</span>
                    </label>
                </div>
            `;
        });

        categoryDiv.innerHTML = itemsHtml;
        categoriesContainer.appendChild(categoryDiv);
    });

    document.getElementById('groceryListDisplay').classList.remove('hidden');
}

function categorizIngredients(groceryList) {
    const categories = {
        'Produce': [],
        'Dairy & Eggs': [],
        'Pantry Staples': [],
        'Spices & Seasonings': [],
        'Other': []
    };

    // Simple keyword-based categorization
    const produce = ['vegetable', 'fruit', 'lettuce', 'tomato', 'onion', 'garlic', 'pepper', 'carrot'];
    const dairy = ['milk', 'butter', 'cheese', 'egg', 'yogurt', 'cream'];
    const pantry = ['flour', 'sugar', 'salt', 'oil', 'rice', 'pasta', 'bean'];
    const spices = ['salt', 'pepper', 'spice', 'herb', 'paprika', 'cumin', 'oregano'];

    Object.entries(groceryList).forEach(([ingredient, count]) => {
        const lower = ingredient.toLowerCase();
        let categorized = false;

        for (const key of produce) {
            if (lower.includes(key)) {
                categories['Produce'].push({ name: ingredient, count });
                categorized = true;
                break;
            }
        }

        if (!categorized) {
            for (const key of dairy) {
                if (lower.includes(key)) {
                    categories['Dairy & Eggs'].push({ name: ingredient, count });
                    categorized = true;
                    break;
                }
            }
        }

        if (!categorized) {
            for (const key of pantry) {
                if (lower.includes(key)) {
                    categories['Pantry Staples'].push({ name: ingredient, count });
                    categorized = true;
                    break;
                }
            }
        }

        if (!categorized) {
            for (const key of spices) {
                if (lower.includes(key)) {
                    categories['Spices & Seasonings'].push({ name: ingredient, count });
                    categorized = true;
                    break;
                }
            }
        }

        if (!categorized) {
            categories['Other'].push({ name: ingredient, count });
        }
    });

    // Remove empty categories
    Object.keys(categories).forEach((cat) => {
        if (categories[cat].length === 0) {
            delete categories[cat];
        }
    });

    return categories;
}

function exportGroceryList() {
    const items = [];
    document.querySelectorAll('.grocery-item label').forEach((label) => {
        items.push(label.textContent.trim());
    });

    const text = items.join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'grocery-list.txt';
    a.click();
    window.URL.revokeObjectURL(url);
}

function clearGroceryList() {
    document.getElementById('groceryListDisplay').classList.add('hidden');
    document.getElementById('groceryCategories').innerHTML = '';
}
