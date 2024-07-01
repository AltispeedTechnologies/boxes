const globals = require("./node_modules/globals/index.js");

module.exports = {
    languageOptions: {
        ecmaVersion: "latest",
        sourceType: "script",
        globals: {
            "Chart": false,
            "Turbo": false,
            ...globals.browser,
            ...globals.jquery,
            ...globals.amd,
            ...globals.commonjs
        }
    },
    rules: {
        indent: ["error", 4],
        quotes: ["error", "double"],
        semi: ["error", "always"],
        "no-unused-vars": ["warn"],
        "no-undef": ["error"],
        "eqeqeq": ["error", "always"],
        "no-trailing-spaces": ["error"],
        "space-infix-ops": ["error"],
        "no-multi-spaces": ["error", { ignoreEOLComments: false }],
        "space-before-blocks": ["error"]
    }
};
