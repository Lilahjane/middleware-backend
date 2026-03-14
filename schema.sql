-- JUST MEAL PLANNER - Database Schema
-- PostgreSQL
-- Updated: 2026-03-14
-- ============================================================================
-- PHASE 1: Core Recipe Data
-- ============================================================================
CREATE TABLE recipes (
    recipe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    source_url TEXT,
    yield_servings INTEGER,
    cook_time_minutes INTEGER,
    prep_time_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_recipes_id ON recipes(recipe_id);
CREATE INDEX idx_recipes_title ON recipes(title);
CREATE TABLE ingredients (
    ingredient_id VARCHAR(64) PRIMARY KEY,
    -- "ing_ham_serrano_001"
    canonical_name VARCHAR(255) NOT NULL,
    category VARCHAR(128),
    type VARCHAR(128),
    aliases_json JSONB,
    -- Denormalized for fast lookup
    metadata_json JSONB,
    -- Region, preservation_method, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ingredients_id ON ingredients(ingredient_id);
CREATE INDEX idx_ingredients_canonical_name ON ingredients USING GIN(to_tsvector('english', canonical_name));
CREATE INDEX idx_ingredients_type ON ingredients(type);
CREATE INDEX idx_ingredients_category ON ingredients(category);
CREATE TABLE recipe_ingredients (
    recipe_ingredient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_id VARCHAR(64) NOT NULL REFERENCES ingredients(ingredient_id),
    display_text TEXT,
    -- "1.5 cups finely diced"
    parsed_amount_data JSONB NOT NULL,
    -- {type, aggregation_type, quantity, unit, metric_ml, total_count}
    parsed_preparation VARCHAR(255),
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);
CREATE INDEX idx_recipe_ingredients_recipe_sort ON recipe_ingredients(recipe_id, sort_order);
-- ============================================================================
-- PHASE 2: Logistics & Math for Grocery Lists
-- ============================================================================
CREATE TABLE ingredient_conversions (
    conversion_id SERIAL PRIMARY KEY,
    ingredient_id VARCHAR(64) NOT NULL REFERENCES ingredients(ingredient_id),
    from_unit VARCHAR(32) NOT NULL,
    -- "cup"
    to_unit VARCHAR(32) NOT NULL,
    -- "gram"
    conversion_factor DECIMAL(10, 4) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_conversions_ingredient_id ON ingredient_conversions(ingredient_id);
CREATE INDEX idx_conversions_units ON ingredient_conversions(from_unit, to_unit);
CREATE TABLE grocery_lists (
    grocery_list_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    -- NULL for Phase 1-2, used in Phase 3
    name VARCHAR(255),
    -- "Weekly Shopping"
    created_from_recipes UUID [] DEFAULT '{}',
    -- Array of recipe IDs
    status VARCHAR(32) DEFAULT 'draft',
    -- "draft", "ready", "completed"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_grocery_lists_user_id ON grocery_lists(user_id);
CREATE INDEX idx_grocery_lists_status ON grocery_lists(status);
CREATE TABLE grocery_list_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grocery_list_id UUID NOT NULL REFERENCES grocery_lists(grocery_list_id) ON DELETE CASCADE,
    ingredient_id VARCHAR(64) NOT NULL REFERENCES ingredients(ingredient_id),
    total_quantity DECIMAL(12, 4),
    unit VARCHAR(32),
    metric_ml_equivalent DECIMAL(12, 4),
    -- For volume items
    total_count_equivalent DECIMAL(12, 4),
    -- For count items
    aggregation_source JSONB,
    -- [{recipe_id, original_qty, unit}]
    checked_off BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_grocery_list_items_list_id ON grocery_list_items(grocery_list_id);
CREATE INDEX idx_grocery_list_items_ingredient_id ON grocery_list_items(ingredient_id);
-- ============================================================================
-- PHASE 3: User Features & Preferences
-- ============================================================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(128) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    dietary_restrictions JSONB DEFAULT '[]'::jsonb,
    -- ["gluten-free", "vegan"]
    allergies JSONB DEFAULT '[]'::jsonb,
    -- ["peanuts", "shellfish"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE TABLE user_ingredient_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ingredient_id VARCHAR(64) NOT NULL REFERENCES ingredients(ingredient_id),
    custom_aliases JSONB DEFAULT '[]'::jsonb,
    -- ["my ham", "my jamón"]
    is_available BOOLEAN DEFAULT true,
    is_allergic BOOLEAN DEFAULT false,
    preferred_substitute_id VARCHAR(64) REFERENCES ingredients(ingredient_id),
    custom_notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, ingredient_id)
);
CREATE INDEX idx_user_prefs_user_id ON user_ingredient_preferences(user_id);
CREATE INDEX idx_user_prefs_ingredient_id ON user_ingredient_preferences(ingredient_id);
CREATE TABLE user_ingredient_corrections (
    correction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ingredient_id VARCHAR(64) NOT NULL REFERENCES ingredients(ingredient_id),
    issue_type VARCHAR(64),
    -- "wrong_category", "missing_alias", "incorrect_substitution"
    description TEXT,
    votes_agree INTEGER DEFAULT 0,
    votes_disagree INTEGER DEFAULT 0,
    status VARCHAR(32) DEFAULT 'pending',
    -- "pending", "approved", "rejected", "merged"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
CREATE INDEX idx_user_corrections_ingredient_id ON user_ingredient_corrections(ingredient_id);
CREATE INDEX idx_user_corrections_status ON user_ingredient_corrections(status);
CREATE INDEX idx_user_corrections_votes ON user_ingredient_corrections(votes_agree DESC);
CREATE TABLE meal_plans (
    meal_plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_meal_plans_user_id ON meal_plans(user_id);
CREATE INDEX idx_meal_plans_date_range ON meal_plans(start_date, end_date);
CREATE TABLE meal_plan_recipes (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_plan_id UUID NOT NULL REFERENCES meal_plans(meal_plan_id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(recipe_id),
    day_number INTEGER,
    -- 0-6 for week, or day offset
    meal_type VARCHAR(32),
    -- "breakfast", "lunch", "dinner", "snack"
    servings_to_make INTEGER,
    -- Override recipe yield
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_meal_plan_recipes_plan_id ON meal_plan_recipes(meal_plan_id);
CREATE INDEX idx_meal_plan_recipes_day ON meal_plan_recipes(meal_plan_id, day_number);
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(128),
    record_id VARCHAR(255),
    action VARCHAR(32),
    -- "INSERT", "UPDATE", "DELETE"
    changed_fields JSONB,
    user_id UUID REFERENCES users(user_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);
CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
-- ============================================================================
-- SUMMARY OF TABLES
-- ============================================================================
-- Phase 1:     recipes, ingredients, recipe_ingredients (3 tables)
-- Phase 1+2:   ingredient_conversions, grocery_lists, grocery_list_items (6 total)
-- Phase 3:     users, user_ingredient_preferences, user_ingredient_corrections,
--              meal_plans, meal_plan_recipes, audit_log (12 total)
-- ============================================================================