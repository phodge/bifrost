# Defining / Serving a Collection


## PHP

You define a collection by building a PHP class like this:

    <?php

	namespace MyCollections;

	class RegexFunctions extends Bifrost\SimpleCollection; {
		function getExportedFunctions() {
			return [
				'preg_match',
				'\MyNamespace\SomeOtherFunction',
			];
		}

		function getExportedClasses() {
			// TODO: describe how to do the same for classes
			return [
				'\DateTime';
			];
		}

		function getExportedVariables() {
			// TODO: describe how to do the same for classes
			return [
				'_SESSION' => $_SESSION;
			];
		}
	}

You can start up a [Server] processes that hosts this collection using the following command.

You can export a *Consumer Library* for this collection like this:

	$ bifrost generate-php-consumer --from 'MyCollections\\RegexFunctions' --to
	'MyCollections\APIs\RegexFunctions';


