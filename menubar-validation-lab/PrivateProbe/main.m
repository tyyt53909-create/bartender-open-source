#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <dlfcn.h>
#include <stdio.h>

// ONLY availability inspection. No assertion allocation, activate call,
// objc_msgSend, or private preference-write calls are made by this probe.
int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSString *path = @"/System/Library/PrivateFrameworks/MenuBarClientCore.framework/MenuBarClientCore";
        void *handle = dlopen(path.fileSystemRepresentation, RTLD_LAZY | RTLD_LOCAL);
        Class configuration = NSClassFromString(@"MBAssessmentModeConfiguration");
        Class assertion = NSClassFromString(@"MBAssessmentModeAssertion");
        BOOL initAvailable = configuration && [configuration instancesRespondToSelector:
            NSSelectorFromString(@"initWithAllowedSystemItems:allowedBundleIdentifiers:")];
        BOOL activateAvailable = assertion && [assertion instancesRespondToSelector:
            NSSelectorFromString(@"activateWithConfiguration:completionHandler:")];
        BOOL invalidateAvailable = assertion && [assertion instancesRespondToSelector:
            NSSelectorFromString(@"invalidate")];
        NSDictionary *record = @{
            @"schema": @"menuvalidation.private-probe.v1",
            @"timestamp": [[[NSISO8601DateFormatter alloc] init] stringFromDate:NSDate.date],
            @"backend_id": @"private_readonly_probe",
            @"os": NSProcessInfo.processInfo.operatingSystemVersionString,
            @"framework_loaded": @(handle != NULL),
            @"configuration_init_present": @(initAvailable),
            @"activate_selector_present": @(activateAvailable),
            @"invalidate_selector_present": @(invalidateAvailable),
            @"assertion_activated": @NO,
            @"evidence_level": @"symbol_availability_only",
            @"behavior_verdict": @"not_run",
            @"limitations": @[
                @"No private visibility operation was performed.",
                @"Selector presence does not verify signatures, callbacks, recovery or OS support.",
                @"System-item IDs, app location and privacy indicators remain unresolved."
            ]
        };
        NSError *error = nil;
        NSData *data = [NSJSONSerialization dataWithJSONObject:record
            options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:&error];
        if (!data) { fprintf(stderr, "Could not encode probe result.\n"); return 1; }
        fwrite(data.bytes, 1, data.length, stdout);
        fputc('\n', stdout);
        return 0;
    }
}

